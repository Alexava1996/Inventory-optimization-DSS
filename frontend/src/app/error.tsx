"use client";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <main className="login">
      <h1>Qualcosa si è interrotto</h1>
      <p>I tuoi dati salvati sono al sicuro. Riprova a caricare la pagina.</p>
      <button onClick={reset}>Riprova</button>
    </main>
  );
}
