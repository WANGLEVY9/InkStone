export const waitForVisibleSelector = (
  selector: string,
  { timeout = 5000, extraDelay = 320 } = {},
): Promise<void> =>
  new Promise((resolve) => {
    const deadline = Date.now() + timeout;

    const poll = () => {
      const el = document.querySelector(selector);
      const rect = el?.getBoundingClientRect();
      const visible = Boolean(rect && rect.width > 0 && rect.height > 0);

      if (visible) {
        if (extraDelay > 0) {
          window.setTimeout(resolve, extraDelay);
        } else {
          resolve();
        }
        return;
      }

      if (Date.now() >= deadline) {
        resolve();
        return;
      }

      window.requestAnimationFrame(poll);
    };

    poll();
  });
