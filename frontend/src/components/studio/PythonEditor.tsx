import { useEffect, useRef } from "react";
import { EditorState } from "@codemirror/state";
import { EditorView, keymap, lineNumbers } from "@codemirror/view";
import { defaultKeymap, history, historyKeymap } from "@codemirror/commands";
import { python } from "@codemirror/lang-python";

type Props = { value: string; onChange(value: string): void; disabled?: boolean };
export default function PythonEditor({ value, onChange, disabled = false }: Props) {
  const host = useRef<HTMLDivElement>(null);
  const view = useRef<EditorView | null>(null);
  const callback = useRef(onChange);
  callback.current = onChange;
  useEffect(() => {
    if (!host.current) return;
    const editor = new EditorView({
      parent: host.current,
      state: EditorState.create({ doc: value, extensions: [lineNumbers(), history(), keymap.of([...defaultKeymap, ...historyKeymap]), python(), EditorView.lineWrapping, EditorState.readOnly.of(disabled), EditorView.editable.of(!disabled), EditorView.updateListener.of((update) => { if (update.docChanged) callback.current(update.state.doc.toString()); })] })
    });
    view.current = editor;
    return () => { editor.destroy(); view.current = null; };
  }, [disabled]);
  useEffect(() => {
    const editor = view.current;
    if (editor && editor.state.doc.toString() !== value) editor.dispatch({ changes: { from: 0, to: editor.state.doc.length, insert: value } });
  }, [value]);
  return <div className="studio-code-editor" ref={host} aria-label="Python source editor" />;
}
