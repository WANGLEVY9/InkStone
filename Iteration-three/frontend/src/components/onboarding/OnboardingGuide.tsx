import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { CSSProperties } from 'react';
import { Button } from 'antd';
import { getTourById, type GuidePlacement, type TourStep } from '@/components/onboarding/tourConfig';
import { useOnboarding } from '@/contexts/OnboardingContext';

interface GuideLayout {
  position: CSSProperties;
  placement: GuidePlacement;
  targetRect: DOMRect | null;
}

const GUIDE_WIDTH = 300;
const GUIDE_HEIGHT = 156;
const SCREEN_MARGIN = 16;
const TARGET_PADDING = 8;
const GAP = 16;

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);

const canUsePlacement = (rect: DOMRect, placement: GuidePlacement) => {
  if (placement === 'left') return rect.left >= GUIDE_WIDTH + GAP + SCREEN_MARGIN;
  if (placement === 'right') return window.innerWidth - rect.right >= GUIDE_WIDTH + GAP + SCREEN_MARGIN;
  if (placement === 'top') return rect.top >= GUIDE_HEIGHT + GAP + SCREEN_MARGIN;
  if (placement === 'bottom') return window.innerHeight - rect.bottom >= GUIDE_HEIGHT + GAP + SCREEN_MARGIN;
  return true;
};

const choosePlacement = (rect: DOMRect, preferred: GuidePlacement = 'bottom') => {
  if (preferred !== 'center' && canUsePlacement(rect, preferred)) return preferred;
  return (['right', 'left', 'bottom', 'top'] as GuidePlacement[]).find((item) => canUsePlacement(rect, item)) || 'center';
};

const getGuideLayout = (target: Element | null, step: TourStep): GuideLayout => {
  if (!target || step.placement === 'center') {
    return {
      position: { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' },
      placement: 'center',
      targetRect: null,
    };
  }

  const rect = target.getBoundingClientRect();
  const placement = step.forcePlacement ? (step.placement || 'bottom') : choosePlacement(rect, step.placement || 'bottom');
  const offsetY = step.offsetY || 0;

  if (placement === 'left') {
    return {
      position: {
        top: clamp(rect.top + rect.height / 2 - GUIDE_HEIGHT / 2, SCREEN_MARGIN, window.innerHeight - GUIDE_HEIGHT - SCREEN_MARGIN),
        left: Math.max(SCREEN_MARGIN, rect.left - GUIDE_WIDTH - GAP),
      },
      placement,
      targetRect: rect,
    };
  }

  if (placement === 'right') {
    return {
      position: {
        top: clamp(rect.top + rect.height / 2 - GUIDE_HEIGHT / 2, SCREEN_MARGIN, window.innerHeight - GUIDE_HEIGHT - SCREEN_MARGIN),
        left: Math.min(window.innerWidth - GUIDE_WIDTH - SCREEN_MARGIN, rect.right + GAP),
      },
      placement,
      targetRect: rect,
    };
  }

  if (placement === 'top') {
    return {
      position: {
        top: Math.max(SCREEN_MARGIN, rect.top - GUIDE_HEIGHT - GAP - offsetY),
        left: clamp(rect.left + rect.width / 2 - GUIDE_WIDTH / 2, SCREEN_MARGIN, window.innerWidth - GUIDE_WIDTH - SCREEN_MARGIN),
      },
      placement,
      targetRect: rect,
    };
  }

  return {
    position: {
      top: Math.min(window.innerHeight - GUIDE_HEIGHT - SCREEN_MARGIN, rect.bottom + GAP + offsetY),
      left: clamp(rect.left + rect.width / 2 - GUIDE_WIDTH / 2, SCREEN_MARGIN, window.innerWidth - GUIDE_WIDTH - SCREEN_MARGIN),
    },
    placement: 'bottom',
    targetRect: rect,
  };
};

const getArrowStyle = (placement: GuidePlacement): CSSProperties | null => {
  const base: CSSProperties = {
    position: 'absolute',
    width: 14,
    height: 14,
    background: 'var(--paper-elevated)',
    borderColor: 'var(--silk-line-strong)',
    borderStyle: 'solid',
    transform: 'rotate(45deg)',
  };

  if (placement === 'right') return { ...base, left: -8, top: '50%', marginTop: -7, borderWidth: '0 0 1px 1px' };
  if (placement === 'left') return { ...base, right: -8, top: '50%', marginTop: -7, borderWidth: '1px 1px 0 0' };
  if (placement === 'top') return { ...base, bottom: -8, left: '50%', marginLeft: -7, borderWidth: '0 1px 1px 0' };
  if (placement === 'bottom') return { ...base, top: -8, left: '50%', marginLeft: -7, borderWidth: '1px 0 0 1px' };
  return null;
};

const buildMaskRects = (targetRect: DOMRect): CSSProperties[] => {
  const maskBase: CSSProperties = {
    position: 'fixed',
    zIndex: 2500,
    pointerEvents: 'none',
  };
  const top = clamp(targetRect.top - TARGET_PADDING, 0, window.innerHeight);
  const left = clamp(targetRect.left - TARGET_PADDING, 0, window.innerWidth);
  const right = clamp(targetRect.right + TARGET_PADDING, 0, window.innerWidth);
  const bottom = clamp(targetRect.bottom + TARGET_PADDING, 0, window.innerHeight);

  return [
    { ...maskBase, top: 0, left: 0, right: 0, height: top },
    { ...maskBase, top: bottom, left: 0, right: 0, bottom: 0 },
    { ...maskBase, top, left: 0, width: left, height: bottom - top },
    { ...maskBase, top, left: right, right: 0, height: bottom - top },
  ];
};

const isInViewport = (rect: DOMRect) =>
  rect.top >= SCREEN_MARGIN &&
  rect.left >= SCREEN_MARGIN &&
  rect.bottom <= window.innerHeight - SCREEN_MARGIN &&
  rect.right <= window.innerWidth - SCREEN_MARGIN;

const resolveGuideTargets = (step: TourStep) => {
  const target = document.querySelector(step.selector);
  const positionTarget = step.positionSelector
    ? document.querySelector(step.positionSelector)
    : step.interactiveClosest
      ? target?.closest(step.interactiveClosest)
      : target;

  return { target, positionTarget: positionTarget || target };
};

const OnboardingGuide = () => {
  const { active, stepTransitioning, activeTourId, stepIndex, totalSteps, skip, complete, next } = useOnboarding();
  const activeTour = useMemo(() => getTourById(activeTourId), [activeTourId]);
  const currentStep = activeTour?.steps[stepIndex] || null;
  const [position, setPosition] = useState<CSSProperties>({});
  const [placement, setPlacement] = useState<GuidePlacement>('center');
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);
  const [guideReady, setGuideReady] = useState(false);
  const rafRef = useRef<number>();

  const updateLayout = useCallback(() => {
    if (!currentStep) return;

    const { positionTarget } = resolveGuideTargets(currentStep);
    if (!positionTarget) {
      setGuideReady(true);
      return;
    }

    const rawRect = positionTarget.getBoundingClientRect();
    if (!isInViewport(rawRect)) {
      positionTarget.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: 'instant' as ScrollBehavior });
    }

    const layout = getGuideLayout(positionTarget, currentStep);
    const rect = positionTarget.getBoundingClientRect();

    setPosition(layout.position);
    setPlacement(layout.placement);
    setTargetRect(rect.width > 0 && rect.height > 0 ? rect : layout.targetRect);
    setGuideReady(true);
  }, [currentStep]);

  useEffect(() => {
    if (!active || !currentStep) {
      setGuideReady(false);
      return;
    }

    setGuideReady(false);
    let attempts = 0;
    const maxAttempts = currentStep.selector.includes('drawer-new-session') ? 60 : 20;

    const tryUpdate = () => {
      attempts += 1;
      const { positionTarget } = resolveGuideTargets(currentStep);
      if (positionTarget || attempts >= maxAttempts) {
        updateLayout();
        return;
      }
      rafRef.current = window.requestAnimationFrame(tryUpdate);
    };

    rafRef.current = window.requestAnimationFrame(tryUpdate);

    const onResize = () => updateLayout();
    window.addEventListener('resize', onResize);
    window.addEventListener('scroll', onResize, true);

    return () => {
      if (rafRef.current) window.cancelAnimationFrame(rafRef.current);
      window.removeEventListener('resize', onResize);
      window.removeEventListener('scroll', onResize, true);
    };
  }, [active, currentStep, updateLayout]);

  if (stepTransitioning || !active || !activeTour || !currentStep) return null;

  const isLastStep = stepIndex >= totalSteps - 1;
  const showSkip = !isLastStep || activeTourId !== 'chat';
  const arrowStyle = targetRect ? getArrowStyle(placement) : null;
  const guidePosition: CSSProperties = targetRect
    ? position
    : { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' };

  const paddedRect = targetRect
    ? {
        top: Math.max(0, targetRect.top - TARGET_PADDING),
        left: Math.max(0, targetRect.left - TARGET_PADDING),
        width: targetRect.width + TARGET_PADDING * 2,
        height: targetRect.height + TARGET_PADDING * 2,
      }
    : null;

  return (
    <>
      {/* Blocks all page interaction; only the guide panel receives clicks */}
      <div className="onboarding-blocker" aria-hidden="true" />

      {paddedRect ? (
        buildMaskRects(targetRect!).map((style, index) => (
          <div key={index} className="onboarding-mask onboarding-mask-panel" style={style} />
        ))
      ) : (
        <div className="onboarding-mask onboarding-mask-full" />
      )}

      {paddedRect && (
        <div
          className="onboarding-highlight"
          style={{
            top: paddedRect.top,
            left: paddedRect.left,
            width: paddedRect.width,
            height: paddedRect.height,
          }}
        />
      )}

      <div
        className={`onboarding-guide${guideReady ? ' onboarding-guide--ready' : ''}`}
        style={{
          width: GUIDE_WIDTH,
          minHeight: GUIDE_HEIGHT,
          ...guidePosition,
        }}
      >
        {arrowStyle && <div style={arrowStyle} />}
        <div className="onboarding-guide__title">{currentStep.title}</div>
        <div className="onboarding-guide__content">{currentStep.content}</div>
        <div className="onboarding-guide__footer">
          <span className="onboarding-guide__step text-caption">
            {stepIndex + 1} / {totalSteps}
          </span>
          <div className="onboarding-guide__actions">
            {showSkip && (
              <Button type="link" size="small" onClick={skip}>
                跳过
              </Button>
            )}
            {!isLastStep && (
              <Button type="primary" size="small" onClick={next}>
                确定
              </Button>
            )}
            {isLastStep && (
              <Button type="primary" size="small" onClick={complete}>
                完成
              </Button>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default OnboardingGuide;
