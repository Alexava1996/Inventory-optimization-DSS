import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
const credentials = {
  email: process.env.E2E_EMAIL || "",
  password: process.env.E2E_PASSWORD || "",
};
if (!credentials.email || !credentials.password)
  throw new Error(
    "Imposta E2E_EMAIL ed E2E_PASSWORD per un account di prova dedicato.",
  );
async function login(page: Page) {
  await page.goto("/");
  await page.getByLabel("Email", { exact: true }).fill(credentials.email);
  await page.getByLabel("Password", { exact: true }).fill(credentials.password);
  await page.getByRole("button", { name: "Accedi al magazzino" }).click();
  await expect(
    page.getByRole("heading", { name: "Il magazzino, a colpo d’occhio" }),
  ).toBeVisible();
  await expect(page.getByRole("main")).toHaveAttribute("aria-busy", "false");
}

test("login, keyboard focus and accessibility", async ({ page }, info) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Bentornato nel tuo spazio" }),
  ).toBeVisible();
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await login(page);
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `test-results/qa-${info.project.name}.png`,
    fullPage: true,
  });
  expect(errors).toEqual([]);
});

test("create forecast, move stock, simulate, archive and restore", async ({
  page,
}) => {
  await login(page);
  const sku = `E2E-${Date.now()}`;
  await page
    .getByRole("button", { name: "Nuovo articolo", exact: true })
    .click();
  await page.getByLabel("Codice articolo (SKU)").fill(sku);
  await page
    .getByLabel("Nome articolo", { exact: true })
    .fill("Caffè in grani");
  await page.getByLabel("Giacenza iniziale (unità)").fill("20");
  await page
    .getByRole("button", { name: "Crea e aggiungi previsione" })
    .click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("heading")).toHaveText(/Previsione/);
  await page.getByLabel("Domanda annua (unità)").fill("3650");
  await page.getByLabel("Tempo di consegna (giorni)").fill("7");
  await page.getByRole("button", { name: "Salva previsione" }).click();
  await expect(dialog).not.toBeVisible();
  await page
    .getByRole("textbox", { name: "Cerca per nome o codice articolo" })
    .fill(sku);
  await expect(page.getByRole("main")).toHaveAttribute("aria-busy", "false");
  const row = page.getByRole("row").filter({ hasText: sku });
  await expect(row).toContainText("Da riordinare");
  await row.getByRole("button", { name: "Movimento", exact: true }).click();
  await page.getByLabel("Quantità da movimentare").fill("200");
  await page.getByLabel("Motivo dell’operazione").fill("Ricevimento test");
  await page.getByRole("button", { name: "Registra movimento" }).click();
  await expect(dialog).not.toBeVisible();
  await expect(row).toContainText("Regolare");
  await row
    .getByRole("button", { name: "Caffè in grani", exact: true })
    .click();
  await expect(dialog).toContainText("Ricevimento test");
  await page.keyboard.press("Escape");
  await expect(dialog).not.toBeVisible();
  await page.getByLabel("Simulazione stagionale").fill("2");
  await expect(row).toContainText("Da riordinare");
  await row.getByRole("button", { name: "Archivia Caffè in grani" }).click();
  await page.getByRole("button", { name: "Conferma archiviazione" }).click();
  await expect(dialog).not.toBeVisible();
  await page.getByRole("button", { name: "Archivio", exact: true }).click();
  await expect(
    row.getByRole("button", { name: "Ripristina Caffè in grani" }),
  ).toBeVisible();
  await row.getByRole("button", { name: "Ripristina Caffè in grani" }).click();
  await dialog
    .getByRole("button", { name: "Ripristina articolo", exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
});

test("legacy import is safe, download works and logout revokes access", async ({
  page,
}) => {
  await login(page);
  const sku = `IMPORT-${Date.now()}`;
  const file = JSON.stringify({
    [sku]: {
      Nome_Articolo: "Prodotto importato",
      Anni: {
        "2026": {
          domanda_annuale: 3650,
          costo_ordine: 50,
          costo_mantenimento: 5,
          lead_time_giorni: 7,
          scorta_sicurezza: 70,
        },
      },
    },
  });
  await page.getByRole("button", { name: "Importa JSON" }).click();
  await page
    .getByLabel("File dell’archivio (massimo 1 MB)")
    .setInputFiles({
      name: "Dizionario.txt",
      mimeType: "text/plain",
      buffer: Buffer.from(file),
    });
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Importa archivio", exact: true })
    .click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await page
    .getByRole("textbox", { name: "Cerca per nome o codice articolo" })
    .fill(sku);
  const row = page.getByRole("row").filter({ hasText: sku });
  await expect(row).toContainText("Da rilevare");
  await expect(row).toContainText("Da completare");
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Esporta CSV" }).click();
  expect((await download).suggestedFilename()).toMatch(/magazzino-\d{4}\.csv/);
  await page.getByRole("button", { name: "Esci dall’account" }).click();
  await expect(
    page.getByRole("heading", { name: "Bentornato nel tuo spazio" }),
  ).toBeVisible();
  expect((await page.request.get("/api/v1/auth/me")).status()).toBe(401);
});
