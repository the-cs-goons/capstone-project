import React from "react";
import App from "~/root";
import { render, screen } from "@testing-library/react";

test("renders learn react link", () => {
  render(<App />);
  const element = screen.getAllByRole("generic")[0]; // random letter
  expect(element).toBeInTheDocument();
});
