import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

// Limpia el DOM tras cada test para que no haya residuos entre runs
afterEach(() => {
  cleanup();
});
