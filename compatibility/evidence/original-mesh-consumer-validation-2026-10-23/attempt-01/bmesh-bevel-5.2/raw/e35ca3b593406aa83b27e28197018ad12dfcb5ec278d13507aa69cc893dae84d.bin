"use strict";

// Evidence-only launcher. The original Python driver and helper are never wrapped.
// The original module's automatic main receives the original native argv strings.
(() => {
  const marker = "BEVEL_BROWSER_EVENT ";
  const state = window.__bevelEvidence = {
    schema: 1, events: [], runtimeExitCodes: [], aborts: [], errors: [],
    automaticMain: true, manualMainCalls: 0, runtimeInitialized: false,
    moduleResolved: false, finished: false,
  };
  function emit(kind, detail) {
    const event = {sequence: state.events.length, milliseconds: performance.now(), kind, detail};
    state.events.push(event);
    console.log(marker + JSON.stringify(event));
  }
  function fail(error) {
    const detail = {name: error?.name || "Error", message: String(error?.message || error),
                    stack: String(error?.stack || "")};
    state.errors.push(detail);
    emit("launcher_error", detail);
    state.finished = true;
  }
  function sameBytes(actual, expected) {
    if (actual.length !== expected.length) return false;
    for (let i = 0; i < actual.length; ++i) if (actual[i] !== expected[i]) return false;
    return true;
  }
  function inspectFiles(mod, inputs) {
    return inputs.map(({row, bytes}) => {
      const actual = mod.FS.readFile(row.virtual_path, {encoding: "binary"});
      return {virtual_path: row.virtual_path, bytes: actual.length,
              sha256_of_verified_input: row.sha256,
              byte_for_byte_equal_to_verified_input: sameBytes(actual, bytes)};
    });
  }
  async function main() {
    const response = await fetch("/input-manifest.json", {cache: "no-store"});
    if (!response.ok) throw new Error("input manifest HTTP " + response.status);
    const manifest = await response.json();
    if (manifest.command.at(-1) !== "--run-all-tests" || manifest.command.at(-2) !== "--") {
      throw new Error("the original comparison-enabling argument tail is missing");
    }
    const forbidden = ["BLENDER_TEST_UPDATE", "BLENDER_VERBOSE"];
    for (const name of forbidden) {
      if (Object.prototype.hasOwnProperty.call(manifest.environment, name)) {
        throw new Error("forbidden environment key is present: " + name);
      }
    }
    const inputs = [];
    for (const row of manifest.files) {
      const inputResponse = await fetch(row.url, {cache: "no-store"});
      if (!inputResponse.ok) throw new Error("input HTTP " + inputResponse.status + ": " + row.url);
      const bytes = new Uint8Array(await inputResponse.arrayBuffer());
      const hash = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
                             x => x.toString(16).padStart(2, "0")).join("");
      if (hash !== row.sha256 || bytes.length !== row.bytes) {
        throw new Error("input bytes differ from original: " + row.virtual_path);
      }
      inputs.push({row, bytes});
      emit("fetched_original_input", {virtual_path: row.virtual_path, bytes: bytes.length, sha256: hash});
    }
    state.originalCommand = manifest.command.slice();
    state.requestedCwd = manifest.cwd;
    const config = {
      thisProgram: manifest.command[0],
      arguments: manifest.command.slice(1),
      canvas: document.getElementById("canvas"),
      locateFile: path => "/bin/" + path,
      noExitRuntime: false,
      print: line => {
        emit("stdout", String(line));
        if (String(line) === "Blender quit") {
          state.originalQuitObservations = (state.originalQuitObservations || 0) + 1;
          state.originalQuitStdoutSequence = state.events.at(-1).sequence;
          try {
            state.mountedFilesAtOriginalQuit = inspectFiles(config, inputs);
            emit("original_inputs_observed_at_original_quit", {
              original_quit_stdout_sequence: state.originalQuitStdoutSequence,
              files: state.mountedFilesAtOriginalQuit,
              boundary: "original Blender quit stdout before Emscripten runtime teardown",
            });
          } catch (error) {
            state.originalQuitFileObservationError = String(error);
            emit("original_quit_file_observation_error", String(error));
          }
        }
      },
      printErr: line => emit("stderr", String(line)),
      preRun: [mod => {
        if (!mod.ENV || !mod.FS_createPath || !mod.FS_createDataFile) {
          throw new Error("required original Emscripten preload interfaces are absent");
        }
        Object.assign(mod.ENV, manifest.environment);
        for (const name of forbidden) {
          if (Object.prototype.hasOwnProperty.call(mod.ENV, name)) {
            throw new Error("forbidden environment key is present before main: " + name);
          }
        }
        state.preMainEnvironment = {...mod.ENV};
        state.forbiddenEnvironmentKeysAbsent = forbidden.every(name =>
          !Object.prototype.hasOwnProperty.call(mod.ENV, name));
        const directories = new Set();
        const paths = [...inputs.map(input => input.row.virtual_path), manifest.cwd + "/__cwd__"];
        for (const path of paths) {
          if (!path.startsWith("/") || path.includes("/../") || path.includes("\\")) {
            throw new Error("unsafe virtual path: " + path);
          }
          let parent = "";
          for (const part of path.split("/").filter(Boolean).slice(0, -1)) {
            parent += "/" + part;
            directories.add(parent);
          }
        }
        for (const directory of [...directories].sort((a, b) =>
          a.split("/").length - b.split("/").length || a.localeCompare(b))) {
          const slash = directory.lastIndexOf("/");
          mod.FS_createPath(directory.slice(0, slash) || "/", directory.slice(slash + 1), true, true);
        }
        for (const {row, bytes} of inputs) {
          const slash = row.virtual_path.lastIndexOf("/");
          mod.FS_createDataFile(row.virtual_path.slice(0, slash), row.virtual_path.slice(slash + 1),
                                bytes, true, true, true);
        }
        emit("original_inputs_queued_before_main", {count: inputs.length,
             environment: state.preMainEnvironment, forbidden_keys_absent: state.forbiddenEnvironmentKeysAbsent});
      }],
      onRuntimeInitialized: () => {
        const mounted = inspectFiles(config, inputs);
        state.mountedFilesBeforeMain = mounted;
        if (!mounted.every(row => row.byte_for_byte_equal_to_verified_input)) {
          throw new Error("mounted source or oracle bytes differ before main");
        }
        config.FS.chdir(manifest.cwd);
        state.actualCwdBeforeMain = config.FS.cwd();
        if (state.actualCwdBeforeMain !== manifest.cwd) throw new Error("original cwd was not preserved");
        state.argumentTailBeforeAutomaticMain = config.arguments.slice();
        if (JSON.stringify(state.argumentTailBeforeAutomaticMain) !== JSON.stringify(manifest.command.slice(1))) {
          throw new Error("original argument tail changed before automatic main");
        }
        state.runtimeInitialized = true;
        emit("verified_original_inputs_before_main", {files: mounted, cwd: state.actualCwdBeforeMain,
             argument_tail: state.argumentTailBeforeAutomaticMain});
      },
      onAbort: what => {
        state.aborts.push(String(what));
        emit("runtime_abort", String(what));
        state.finished = true;
      },
      onExit: code => {
        state.runtimeExitCodes.push(code);
        state.actualArgvAtRuntimeExit = config.arguments.slice();
        emit("runtime_exit", {code, actual_argv: state.actualArgvAtRuntimeExit,
             filesystem_capture_boundary: "original Blender quit stdout before runtime teardown",
             original_quit_stdout_sequence: state.originalQuitStdoutSequence});
        state.finished = true;
      },
    };
    state.crossOriginIsolated = crossOriginIsolated;
    state.userAgent = navigator.userAgent;
    emit("launch_original_main", {command: manifest.command, cwd: manifest.cwd,
         cross_origin_isolated: crossOriginIsolated, automatic_main: true});
    const mod = await createBlenderModule(config);
    window.__bevelModule = mod;
    state.moduleResolved = true;
    state.actualArgvAfterFactoryResolution = config.arguments.slice();
    emit("module_resolved", {actual_argv: state.actualArgvAfterFactoryResolution});
  }
  main().catch(fail);
})();
