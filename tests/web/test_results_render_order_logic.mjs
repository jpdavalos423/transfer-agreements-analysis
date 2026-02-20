import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";

import { renderResults } from "../../apps/web/results_view.js";

class FakeElement {
  constructor(tagName) {
    this.tagName = tagName;
    this.children = [];
    this.className = "";
    this._textContent = "";
  }

  appendChild(child) {
    this.children.push(child);
    return child;
  }

  set textContent(value) {
    this._textContent = String(value);
  }

  get textContent() {
    return this._textContent;
  }

  set innerHTML(value) {
    if (value === "") {
      this.children = [];
      this._textContent = "";
      return;
    }
    throw new Error("FakeElement only supports clearing innerHTML with empty string.");
  }
}

function makeFakeDocument() {
  return {
    createElement(tagName) {
      return new FakeElement(tagName);
    },
  };
}

function collectByClass(root, className) {
  const out = [];
  const stack = [root];
  while (stack.length > 0) {
    const node = stack.pop();
    if (node.className === className) {
      out.push(node);
    }
    for (let i = node.children.length - 1; i >= 0; i -= 1) {
      stack.push(node.children[i]);
    }
  }
  return out;
}

test("renderResults preserves API-provided term/course ordering using fixture response", () => {
  const fixturePath = path.resolve(
    process.cwd(),
    "tests/fixtures/web/results_fixture_response.json",
  );
  const payload = JSON.parse(fs.readFileSync(fixturePath, "utf-8"));

  const originalDocument = globalThis.document;
  globalThis.document = makeFakeDocument();

  try {
    const container = new FakeElement("div");
    renderResults(container, payload);

    const termTitles = collectByClass(container, "term-title").map((el) => el.textContent);
    assert.deepEqual(termTitles, ["Term 3", "Term 1"]);

    const courseCodes = collectByClass(container, "course-code").map((el) => el.textContent);
    assert.deepEqual(courseCodes, ["ZOO 10", "BIO 20", "ENG 1A", "MATH 1A"]);
  } finally {
    globalThis.document = originalDocument;
  }
});
