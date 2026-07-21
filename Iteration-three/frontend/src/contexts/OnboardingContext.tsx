import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { useLocation } from 'react-router-dom';
import { requestChatDrawerOpen } from '@/components/onboarding/chatDrawerBridge';
import { waitForVisibleSelector } from '@/components/onboarding/onboardingUtils';
import { getTourById, getToursForPath, TOUR_STORAGE_KEYS, type TourId } from '@/components/onboarding/tourConfig';

export type OnboardingStep = string | 'idle' | 'done';

interface OnboardingContextValue {
  active: boolean;
  stepTransitioning: boolean;
  activeTourId: TourId | null;
  step: OnboardingStep;
  stepIndex: number;
  totalSteps: number;
  skip: () => void;
  complete: () => void;
  goToStep: (step: OnboardingStep) => void;
  next: () => void;
}

const OnboardingContext = createContext<OnboardingContextValue | null>(null);

export { TOUR_STORAGE_KEYS };

export const isTourTriggered = (tourId: TourId) =>
  localStorage.getItem(TOUR_STORAGE_KEYS[tourId]) === 'true';

export const markTourTriggered = (tourId: TourId) => {
  localStorage.setItem(TOUR_STORAGE_KEYS[tourId], 'true');
};

export const OnboardingProvider = ({ children }: { children: ReactNode }) => {
  const location = useLocation();
  const [activeTourId, setActiveTourId] = useState<TourId | null>(null);
  const [stepIndex, setStepIndex] = useState(0);
  const [stepTransitioning, setStepTransitioning] = useState(false);

  const activeTour = useMemo(() => getTourById(activeTourId), [activeTourId]);
  const currentStep = activeTour?.steps[stepIndex] || null;
  const step: OnboardingStep = currentStep?.id || (activeTourId ? 'done' : 'idle');
  const active = Boolean(activeTour && currentStep && !stepTransitioning);
  const totalSteps = activeTour?.steps.length || 0;

  const complete = useCallback(() => {
    if (activeTourId) markTourTriggered(activeTourId);
    setActiveTourId(null);
    setStepIndex(0);
  }, [activeTourId]);

  const skip = useCallback(() => {
    complete();
  }, [complete]);

  const goToStep = useCallback((nextStep: OnboardingStep) => {
    if (!activeTour) return;
    const nextIndex = activeTour.steps.findIndex((item) => item.id === nextStep);
    if (nextIndex >= 0) {
      setStepIndex(nextIndex);
    }
  }, [activeTour]);

  const next = useCallback(() => {
    if (!activeTour || !activeTourId || stepTransitioning) return;

    const nextIndex = stepIndex + 1;
    if (nextIndex >= activeTour.steps.length) {
      markTourTriggered(activeTourId);
      setActiveTourId(null);
      setStepIndex(0);
      return;
    }

    const leavingStep = activeTour.steps[stepIndex];
    if (leavingStep?.openChatDrawerOnNext) {
      setStepTransitioning(true);
      void (async () => {
        try {
          await requestChatDrawerOpen();
          if (leavingStep.waitForSelector) {
            await waitForVisibleSelector(leavingStep.waitForSelector);
          }
          setStepIndex(nextIndex);
        } finally {
          setStepTransitioning(false);
        }
      })();
      return;
    }

    setStepIndex(nextIndex);
  }, [activeTour, activeTourId, stepIndex, stepTransitioning]);

  useEffect(() => {
    const toursForPath = getToursForPath(location.pathname);
    const pendingTour = toursForPath.find((tour) => !isTourTriggered(tour.id));

    if (activeTourId) {
      const currentTour = getTourById(activeTourId);
      if (currentTour?.match(location.pathname)) return;
      setActiveTourId(null);
      setStepIndex(0);
      return;
    }

    if (!pendingTour) return;

    const timer = window.setTimeout(() => {
      setActiveTourId((current) => {
        if (current) return current;
        if (isTourTriggered(pendingTour.id)) return null;
        return pendingTour.id;
      });
      setStepIndex(0);
    }, 50);

    return () => window.clearTimeout(timer);
  }, [location.pathname, activeTourId]);

  const value = useMemo(
    () => ({
      active,
      stepTransitioning,
      activeTourId,
      step,
      stepIndex,
      totalSteps,
      skip,
      complete,
      goToStep,
      next,
    }),
    [active, stepTransitioning, activeTourId, step, stepIndex, totalSteps, skip, complete, goToStep, next],
  );

  return <OnboardingContext.Provider value={value}>{children}</OnboardingContext.Provider>;
};

export const useOnboarding = () => {
  const value = useContext(OnboardingContext);
  if (!value) {
    throw new Error('useOnboarding must be used within OnboardingProvider');
  }
  return value;
};
