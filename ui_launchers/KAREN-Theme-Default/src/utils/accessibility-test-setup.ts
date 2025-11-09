"use client";
/**
 * Accessibility Test Setup & Configuration (Vitest + Testing Library + axe-core)
 *
 * - Works in JSDOM under Vitest (no jest-axe dependency)
 * - Ships consistent configs (basic/standard/comprehensive + domain-specific)
 * - Helpful error output using Testing Library's prettyDOM tree
 * - Reusable wrapper factory to provide landmarks/skip-links
 * - One-call runner: runAccessibilityTestSuite(container, "standard")
 * - Lightweight pattern validators for common A11Y pitfalls
 * - Optional matcher registration: toHaveNoViolations()
 */

import React from "react";
import { configure } from "@testing-library/react";
import * as dom from "@testing-library/dom";
import axeCore, { AxeResults, RunOptions } from "axe-core";

// ---------------------------------------------------------------------------
// Testing Library configuration
// ---------------------------------------------------------------------------
configure({
  defaultHidden: true,
  asyncUtilTimeout: 10_000,
  getElementError: (message, container) => {
    const tree = dom.prettyDOM(container as HTMLElement, undefined, {
      highlight: false,
      maxDepth: 3,
    });
    const error = new Error(
      [message, "Accessible subtree:", tree].filter(Boolean).join("\n\n")
    );
    error.name = "TestingLibraryElementError";
    return error;
  },
});

// ---------------------------------------------------------------------------
// axe-core configuration presets
// ---------------------------------------------------------------------------
export const accessibilityConfigs = {
  basic: {
    runOnly: { type: "tag" as const, values: ["wcag2a"] },
  },
  standard: {
    runOnly: { type: "tag" as const, values: ["wcag2a", "wcag2aa"] },
  },
  comprehensive: {
    runOnly: { type: "tag" as const, values: ["wcag2a", "wcag2aa", "wcag21aa", "best-practice"] },
  },
  forms: {
    runOnly: { type: "tag" as const, values: ["wcag2a", "wcag2aa"] },
    rules: { "label": { enabled: true } },
  },
  navigation: {
    runOnly: { type: "tag" as const, values: ["wcag2a", "wcag2aa"] },
  },
  visual: {
    runOnly: { type: "tag" as const, values: ["wcag2a", "wcag2aa"] },
  },
};
export type AccessibilityConfigKey = keyof typeof accessibilityConfigs;

// ---------------------------------------------------------------------------
// Wrapper factory: provides language, landmarks, and optional skip-links
// ---------------------------------------------------------------------------
export const createAccessibilityTestWrapper = (options: {
  lang?: string;
  title?: string;
  skipLinks?: boolean;
} = {}) => {
  const { lang = "en", title = "Test Page", skipLinks = false } = options;

  return function AccessibilityTestWrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      "div",
      { lang },
      skipLinks &&
        React.createElement(
          "div",
          null,
          React.createElement(
            "a",
            { href: "#main-content", className: "sr-only focus:not-sr-only" },
            "Skip to main content"
          ),
          React.createElement(
            "a",
            { href: "#navigation", className: "sr-only focus:not-sr-only" },
            "Skip to navigation"
          )
        ),
      React.createElement(
        "nav",
        { id: "navigation", role: "navigation", "aria-label": "Primary" },
        React.createElement("span", null)
      ),
      React.createElement(
        "main",
        { id: "main-content", role: "main" },
        React.createElement("h1", null, title),
        children
      )
    );
  };
};

// ---------------------------------------------------------------------------
// Axe runner (Vitest-compatible). Accepts container and preset key.
// ---------------------------------------------------------------------------
export interface A11yRunReport {
  passed: boolean;
  violations: AxeResults["violations"];
  passes: AxeResults["passes"];
  incomplete: AxeResults["incomplete"];
  inapplicable: AxeResults["inapplicable"];
  summary: {
    violations: number;
    passes: number;
    incomplete: number;
    inapplicable: number;
  };
  config: AccessibilityConfigKey;
  timestamp: string;
}

export const runAccessibilityTestSuite = async (
  container: Element,
  config: AccessibilityConfigKey = "standard",
  overrides?: RunOptions
): Promise<A11yRunReport> => {
  // axe requires a real Node; JSDOM Element is fine
  const options: RunOptions = { ...accessibilityConfigs[config], ...overrides } as RunOptions;
  const results = (await axeCore.run(container as unknown as Node, options)) as AxeResults;

  return {
    passed: results.violations.length === 0,
    violations: results.violations,
    passes: results.passes,
    incomplete: results.incomplete,
    inapplicable: results.inapplicable,
    summary: {
      violations: results.violations.length,
      passes: results.passes.length,
      incomplete: results.incomplete.length,
      inapplicable: results.inapplicable.length,
    },
    config,
    timestamp: new Date().toISOString(),
  };
};

// ---------------------------------------------------------------------------
// Pattern validators (lightweight heuristics for quick checks)
// ---------------------------------------------------------------------------
export const validateAccessibilityPattern = {
  form(container: Element) {
    const issues: string[] = [];

    const inputs = container.querySelectorAll("input, select, textarea");
    inputs.forEach((input, i) => {
      const id = input.getAttribute("id");
      const ariaLabel = input.getAttribute("aria-label");
      const ariaLabelledBy = input.getAttribute("aria-labelledby");
      const hasLabel = id ? container.querySelector(`label[for="${id}"]`) : null;
      if (!ariaLabel && !ariaLabelledBy && !hasLabel) {
        issues.push(`Form control ${i + 1} is missing an accessible name`);
      }
    });

    const fieldsets = container.querySelectorAll("fieldset");
    fieldsets.forEach((fs, i) => {
      if (!fs.querySelector("legend")) issues.push(`Fieldset ${i + 1} is missing a legend`);
    });

    return issues;
  },

  headings(container: Element) {
    const issues: string[] = [];
    const headings = container.querySelectorAll("h1, h2, h3, h4, h5, h6");
    let previousLevel = 0;

    headings.forEach((el, index) => {
      const level = parseInt(el.tagName.charAt(1), 10);
      if (index === 0 && level !== 1) issues.push("First heading should be h1");
      if (previousLevel && level > previousLevel + 1) {
        issues.push(`Heading level jumps from h${previousLevel} to h${level}`);
      }
      if (!el.textContent || !el.textContent.trim()) {
        issues.push(`Heading ${index + 1} is empty`);
      }
      previousLevel = level;
    });

    return issues;
  },

  landmarks(container: Element) {
    const issues: string[] = [];
    const main = container.querySelectorAll("main, [role='main']");
    if (main.length === 0) issues.push("No main landmark found");
    else if (main.length > 1) issues.push("Multiple main landmarks found");

    const navs = container.querySelectorAll("nav, [role='navigation']");
    navs.forEach((nav, i) => {
      const label = nav.getAttribute("aria-label");
      const labelledBy = nav.getAttribute("aria-labelledby");
      if (navs.length > 1 && !label && !labelledBy) {
        issues.push(`Navigation landmark ${i + 1} needs aria-label or aria-labelledby`);
      }
    });

    return issues;
  },

  aria(container: Element) {
    const issues: string[] = [];

    const withRefs = container.querySelectorAll(
      "[aria-describedby], [aria-labelledby], [aria-controls]"
    );
    withRefs.forEach((el, index) => {
      const ids = [
        el.getAttribute("aria-describedby"),
        el.getAttribute("aria-labelledby"),
        el.getAttribute("aria-controls"),
      ]
        .filter(Boolean)
        .join(" ")
        .split(" ")
        .filter(Boolean);

      ids.forEach((id) => {
        if (id && !container.querySelector(`#${id}`)) {
          issues.push(`Element ${index + 1} references non-existent ID: ${id}`);
        }
      });
    });

    const withRoles = container.querySelectorAll("[role]");
    withRoles.forEach((el, index) => {
      const role = el.getAttribute("role");
      if (role && !isValidAriaRole(role)) {
        issues.push(`Element ${index + 1} has invalid ARIA role: ${role}`);
      }
    });

    return issues;
  },
};

// ---------------------------------------------------------------------------
// Minimal ARIA role validator (static allow-list)
// ---------------------------------------------------------------------------
export function isValidAriaRole(role: string): boolean {
  const validRoles = [
    "alert","alertdialog","application","article","banner","button","cell","checkbox","columnheader",
    "combobox","complementary","contentinfo","definition","dialog","directory","document","feed","figure",
    "form","grid","gridcell","group","heading","img","link","list","listbox","listitem","log","main",
    "marquee","math","menu","menubar","menuitem","menuitemcheckbox","menuitemradio","navigation","none",
    "note","option","presentation","progressbar","radio","radiogroup","region","row","rowgroup","rowheader",
    "scrollbar","search","searchbox","separator","slider","spinbutton","status","switch","tab","table",
    "tablist","tabpanel","term","textbox","timer","toolbar","tooltip","tree","treegrid","treeitem",
  ];
  return validRoles.includes(role);
}

// ---------------------------------------------------------------------------
// Optional: Vitest/Jest-style matcher registration
// use: expect(await runAccessibilityTestSuite(...))).toHaveNoViolations()
// ---------------------------------------------------------------------------
export function registerA11yMatchers() {
  const g: any = globalThis as any;
  if (!g.expect || !g.expect.extend) return; // not in a test env
  g.expect.extend({
    async toHaveNoViolations(received: A11yRunReport | AxeResults) {
      const isA11yReport = (o: any) => o && Array.isArray(o.violations);
      const results = isA11yReport(received)
        ? (received as any)
        : ((await axeCore.run(document)) as AxeResults);

      const pass = results.violations.length === 0;
      const message = () => {
        if (pass) return "Expected no violations and found none.";
        const details = results.violations
          .map((v) => `• ${v.id}: ${v.help} (impact: ${v.impact})\n  nodes: ${v.nodes.length}`)
          .join("\n");
        return `Expected 0 violations, found ${results.violations.length}:\n${details}`;
      };

      return { pass, message } as any;
    },
  });
}

// Default export bundle
export default {
  configs: accessibilityConfigs,
  createWrapper: createAccessibilityTestWrapper,
  runTestSuite: runAccessibilityTestSuite,
  validatePattern: validateAccessibilityPattern,
  registerA11yMatchers,
};
