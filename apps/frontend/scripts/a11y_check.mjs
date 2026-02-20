import fs from "node:fs";
import path from "node:path";

const repoRoot = path.resolve(process.cwd(), "..");
const setupPath = path.join(repoRoot, "frontend", "src", "components", "SetupPage.tsx");
const pathwayPath = path.join(repoRoot, "frontend", "src", "components", "PathwayPage.tsx");
const stylesPath = path.join(repoRoot, "frontend", "src", "styles.css");

function read(filePath) {
  return fs.readFileSync(filePath, "utf8");
}

const setup = read(setupPath);
const pathway = read(pathwayPath);
const styles = read(stylesPath);

const checks = [
  {
    id: "focus-visible",
    ok: styles.includes(":focus-visible"),
    message: "styles.css must define focus-visible styles.",
  },
  {
    id: "skip-link-style",
    ok: styles.includes(".skip-link") && styles.includes(".skip-link:focus-visible"),
    message: "styles.css must define skip-link styles.",
  },
  {
    id: "setup-skip-link",
    ok: setup.includes("Skip to planner setup form"),
    message: "SetupPage.tsx must include a skip link.",
  },
  {
    id: "pathway-skip-link",
    ok: pathway.includes("Skip to pathway content"),
    message: "PathwayPage.tsx must include a skip link.",
  },
  {
    id: "labeled-inputs",
    ok:
      setup.includes('label htmlFor="college_id"') &&
      setup.includes('label htmlFor="target_ucs"') &&
      setup.includes('label htmlFor="ge_pattern"') &&
      setup.includes('label htmlFor="completed_courses"'),
    message: "SetupPage.tsx inputs must have labels.",
  },
  {
    id: "multi-select-help",
    ok: setup.includes('aria-describedby="target-ucs-help"'),
    message: "Target UCs multi-select must include aria-describedby help text.",
  },
  {
    id: "mobile-layout",
    ok: styles.includes("@media (max-width: 760px)"),
    message: "styles.css must include mobile media query.",
  },
];

const failed = checks.filter((check) => !check.ok);

if (failed.length > 0) {
  console.error("Accessibility baseline check failed:");
  for (const check of failed) {
    console.error(`- [${check.id}] ${check.message}`);
  }
  process.exit(1);
}

console.log("Accessibility baseline check passed.");
