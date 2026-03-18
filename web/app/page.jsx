import Header from "./header";

export default function Home() {
  return (
    
    <main className="relative flex min-h-screen flex-col items-center justify-center p-24 bg-gray-100">
      <Header />
      <h1 className="text-4xl font-bold text-blue-600">
        Bienvenido al Agente Docente
      </h1>
      <p className="mt-4 text-lg text-gray-700">
        Esta será la página de inicio de sesión y chat.
      </p>
    </main>
  );
}
