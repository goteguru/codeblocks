/* codeblocks.js
 *
 * Progressive enhancement for textareas with data-lang="js"
 * - all <textarea data-lang="js"> blocks will be upgraded to CodeMirror editors
 * - Run button + Output area will be added
 * - code will be executed using eval (shared scope default; optional isolated scope)
 *
 * Dependencies expected on page BEFORE this script:
 *   - CodeMirror core (codemirror.min.js)
 *   - JavaScript mode (mode/javascript/javascript.min.js)
 */

(function () {
  "use strict";

  // -----------------------------
  // Utils
  // -----------------------------

  function isMac() {
    return /Mac|iPhone|iPad|iPod/.test(navigator.platform);
  }

  function safeStringify(value) {
    const seen = new WeakSet();

    return JSON.stringify(
      value,
      function (_key, val) {
        if (typeof val === "bigint") return `${val.toString()}n`;
        if (typeof val === "object" && val !== null) {
          if (seen.has(val)) return "[Circular]";
          seen.add(val);
        }
        if (typeof val === "function") return `[Function ${val.name || "anonymous"}]`;
        if (val instanceof Error) {
          return {
            name: val.name,
            message: val.message,
            stack: val.stack
          };
        }
        return val;
      },
      2
    );
  }

  function formatValue(value) {
    if (value === undefined) return "";
    if (value === null) return "null";
    const t = typeof value;

    if (t === "string") return value;
    if (t === "number" || t === "boolean" || t === "bigint") return String(value);
    if (t === "function") return value.toString();

    try {
      const s = safeStringify(value);
      // fallback if stringify returns undefined 
      return s === undefined ? String(value) : s;
    } catch (_e) {
      try {
        return String(value);
      } catch (_e2) {
        return "[Unformattable value]";
      }
    }
  }

  function ensureClass(el, className, present) {
    if (!el) return;
    if (present) el.classList.add(className);
    else el.classList.remove(className);
  }

  function createRunButton() {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "javascript-run";
    btn.textContent = "Run";
    return btn;
  }

  function createOutputBox() {
    const pre = document.createElement("pre");
    pre.className = "javascript-output";
    pre.textContent = "";
    return pre;
  }

  // -----------------------------
  // evaluation
  // -----------------------------

  function makeConsoleCapture(writeLine) {
    const original = {
      log: console.log,
      warn: console.warn,
      error: console.error
    };

    function joinArgs(args) {
      return args
        .map((a) => (typeof a === "string" ? a : formatValue(a)))
        .join(" ");
    }

    console.log = (...args) => writeLine(joinArgs(args));
    console.warn = (...args) => writeLine("WARN: " + joinArgs(args));
    console.error = (...args) => writeLine("ERROR: " + joinArgs(args));

    return function restore() {
      console.log = original.log;
      console.warn = original.warn;
      console.error = original.error;
    };
  }

  function runCode({ code, scope, writeLine, setErrorState }) {
    // Clear error state before run
    setErrorState(false);

    const restoreConsole = makeConsoleCapture(writeLine);

    try {
      let result;

      if (scope === "isolated") {
        // Attempt some isolation: vars declared via var/let/const inside eval become local to this IIFE.
        // Still can read globals, but won’t leak local bindings to window.
        result = (function () {
          return eval(code);
        })();
      } else {
        // Shared/global: indirect eval runs in global scope.
        // google trick :)
        result = (0, eval)(code);
      }

      if (result !== undefined) 
        writeLine(formatValue(result));

    } catch (e) {
      setErrorState(true);
      const msg = e && e.message ? e.message : String(e);
      const prefix = (e && e.lineNumber) ? `Error in line ${e.lineNumber}` : "Error";
      writeLine(prefix + ": " + msg);
      if (e && !e.lineNumber && e.stack) {
        writeLine(e.stack.split("\n").slice(1,2).join('').split(":").slice(2,4).join(":"));
      }
    } finally {
      restoreConsole();
    }
  }

  // -----------------------------
  // Enhancement / Initialization
  // -----------------------------

  function enhanceTextarea(textarea, index) {
    const lang = (textarea.getAttribute("data-lang") || "").toLowerCase();
    if (lang !== "js" && lang !== "javascript") return null;

    const scope = (textarea.getAttribute("data-scope") || "shared").toLowerCase();
    const effectiveScope = scope === "isolated" ? "isolated" : "shared";

    const isReadOnly = textarea.hasAttribute("data-readonly");

    const wrapper = document.createElement("div");
    wrapper.className = "codeblock";

    const toolbar = document.createElement("div");
    toolbar.className = "codeblock-toolbar";

    const runBtn = createRunButton();
    const output = createOutputBox();

    textarea.parentNode.insertBefore(wrapper, textarea);
    wrapper.appendChild(toolbar);
    wrapper.appendChild(textarea); 

    if (!isReadOnly) toolbar.appendChild(runBtn);
    wrapper.appendChild(output);

    const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    const cmTheme = prefersDark ? "darcula" : "default";

    // Create CodeMirror instance
    const cm = window.CodeMirror.fromTextArea(textarea, {
      mode: "javascript",
      theme: cmTheme,
      lineNumbers: true,
      indentUnit: 2,
      tabSize: 2,
      viewportMargin: Infinity, 
      readOnly: isReadOnly, 
      extraKeys: isReadOnly ? {} : {
        "Ctrl-Enter": () => runCurrent(),
        "Cmd-Enter": () => runCurrent() // mac
      }
    });

    const cmWrapper = cm.getWrapperElement();
    wrapper.insertBefore(cmWrapper, output);

    // Give each block an id for debugging / future features
    const blockId = textarea.id || `codeblock-${index + 1}`;
    if (!textarea.id) textarea.id = blockId;

    function clearOutput() {
      output.textContent = "";
      ensureClass(output, "javascript-error", false);
    }

    function writeLine(s) {
      if (output.textContent.length === 0) output.textContent = String(s);
      else output.textContent += "\n" + String(s);
    }

    function setErrorState(isError) {
      ensureClass(output, "javascript-error", isError);
    }

    function runCurrent() {
      clearOutput();

      const code = cm.getValue();

      runCode({
        code,
        scope: effectiveScope,
        writeLine,
        setErrorState
      });
    }

    runBtn.addEventListener("click", runCurrent);

    // allow Shift+Enter for newline (CodeMirror default is fine),
    return { textarea, cm, runBtn, output, scope: effectiveScope, run: runCurrent };
  }

  function init(root) {
    if (!window.CodeMirror || typeof window.CodeMirror.fromTextArea !== "function") {
      // Fail gracefully: the HTML remains readable; no runtime crash.
      console.warn(
        "codeblocks.js: CodeMirror v5 not found. " +
          "Load codemirror.min.js and mode/javascript/javascript.min.js before codeblocks.js."
      );
      return [];
    }

    const container = root || document;
    const textareas = Array.from(container.querySelectorAll("textarea[data-lang]"));
    const enhanced = [];

    textareas.forEach((ta, i) => {
      const block = enhanceTextarea(ta, i);
      if (block) enhanced.push(block);
    });

    return enhanced;
  }

  // Expose a some API 
  window.CodeBlocks = { init };

  // Auto-init after DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => init(document));
  } else {
    init(document);
  }
})();
