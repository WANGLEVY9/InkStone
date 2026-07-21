import { useEffect, useRef, useCallback, type RefObject } from 'react';
import Vditor from 'vditor';
import 'vditor/dist/index.css';

export type VditorMode = 'ir' | 'wysiwyg';

interface UseVditorOptions {
  containerRef: RefObject<HTMLDivElement | null>;
  value: string;
  onChange: (value: string) => void;
  height?: number | 'auto';
  placeholder?: string;
  mode?: VditorMode;
}

export function useVditor({
  containerRef,
  value,
  onChange,
  height = 'auto',
  placeholder,
  mode = 'ir',
}: UseVditorOptions) {
  const vdRef = useRef<Vditor | null>(null);
  const internalChangeRef = useRef(false);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout>>();

  // Refs for values that change frequently — keep initVditor stable
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  const valueRef = useRef(value);
  valueRef.current = value;

  const placeholderRef = useRef(placeholder);
  placeholderRef.current = placeholder;

  const computeHeight = useCallback((): number => {
    if (typeof height === 'number') return height;
    const container = containerRef.current;
    if (!container) return 600;
    const rect = container.getBoundingClientRect();
    const available = window.innerHeight - rect.top - 16; // 16px bottom margin
    return Math.max(available, 300);
  }, [height, containerRef]);

  const destroyVditor = useCallback(() => {
    if (vdRef.current) {
      vdRef.current.destroy();
      vdRef.current = null;
    }
  }, []);

  // Only depends on mode — recreates editor when switching IR ↔ WYSIWYG
  const initVditor = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;

    destroyVditor();

    const vd = new Vditor(container, {
      mode,
      icon: 'ant',
      outline: { enable: true, position: 'right' },
      cache: { enable: false },
      height: computeHeight(),
      value: valueRef.current,
      placeholder: placeholderRef.current,
      toolbar: [
        'emoji', 'headings', 'bold', 'italic', 'strike', '|',
        'line', 'quote', 'list', 'ordered-list', 'check', '|',
        'code', 'inline-code', 'table', '|',
        'undo', 'redo', '|',
        'edit-mode', 'fullscreen', 'outline',
      ],
      toolbarConfig: { hide: false },
      input: (val) => {
        if (internalChangeRef.current) {
          internalChangeRef.current = false;
          return;
        }
        clearTimeout(debounceTimerRef.current);
        debounceTimerRef.current = setTimeout(() => {
          onChangeRef.current(val);
        }, 200);
      },
      after: () => {
        vdRef.current = vd;
      },
    });
  }, [containerRef, mode, destroyVditor, computeHeight]);

  // Init on mount, destroy on unmount
  useEffect(() => {
    initVditor();
    return () => {
      clearTimeout(debounceTimerRef.current);
      destroyVditor();
    };
  }, [initVditor, destroyVditor]);

  // Sync external value changes into Vditor (e.g. loading new content)
  useEffect(() => {
    const vd = vdRef.current;
    if (!vd) return;
    const currentValue = vd.getValue();
    if (currentValue !== value) {
      internalChangeRef.current = true;
      vd.setValue(value);
    }
  }, [value]);

}
