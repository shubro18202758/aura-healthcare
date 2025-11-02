// Performance optimization utilities
import { useCallback, useRef, useEffect, useState } from 'react';
import React from 'react';

/**
 * Debounced value hook - returns debounced version of a value
 * @param {any} value - Value to debounce
 * @param {number} delay - Delay in milliseconds
 */
export const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
};

/**
 * Debounced callback hook - prevents excessive function calls
 * @param {Function} callback - Function to debounce
 * @param {number} delay - Delay in milliseconds
 */
export const useDebouncedCallback = (callback, delay) => {
  const timeoutRef = useRef(null);

  const debouncedCallback = useCallback((...args) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      callback(...args);
    }, delay);
  }, [callback, delay]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return debouncedCallback;
};

/**
 * Throttle hook - limits function execution rate
 * @param {Function} callback - Function to throttle
 * @param {number} limit - Minimum time between calls in milliseconds
 */
export const useThrottle = (callback, limit) => {
  const inThrottle = useRef(false);

  const throttledCallback = useCallback((...args) => {
    if (!inThrottle.current) {
      callback(...args);
      inThrottle.current = true;
      setTimeout(() => {
        inThrottle.current = false;
      }, limit);
    }
  }, [callback, limit]);

  return throttledCallback;
};

/**
 * Request Animation Frame hook for smooth animations
 * @param {Function} callback - Animation callback
 */
export const useAnimationFrame = (callback) => {
  const requestRef = useRef();
  const previousTimeRef = useRef();

  const animate = useCallback((time) => {
    if (previousTimeRef.current !== undefined) {
      const deltaTime = time - previousTimeRef.current;
      callback(deltaTime);
    }
    previousTimeRef.current = time;
    requestRef.current = requestAnimationFrame(animate);
  }, [callback]);

  useEffect(() => {
    requestRef.current = requestAnimationFrame(animate);
    return () => {
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
      }
    };
  }, [animate]);
};

/**
 * Optimized interval hook - automatically cleans up
 * @param {Function} callback - Function to call on interval
 * @param {number} delay - Delay in milliseconds (null to pause)
 */
export const useInterval = (callback, delay) => {
  const savedCallback = useRef();

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (delay !== null) {
      const id = setInterval(() => savedCallback.current(), delay);
      return () => clearInterval(id);
    }
  }, [delay]);
};

/**
 * Lazy load component with suspense support
 * @param {Function} importFunc - Dynamic import function
 */
export const lazyLoad = (importFunc) => {
  return React.lazy(() => {
    return Promise.all([
      importFunc(),
      new Promise(resolve => setTimeout(resolve, 0)) // Minimum delay for smoother loading
    ]).then(([moduleExports]) => moduleExports);
  });
};

/**
 * Memoize expensive calculations
 * @param {Function} fn - Function to memoize
 * @param {Array} deps - Dependencies array
 */
export const useMemoizedCallback = (fn, deps) => {
  // eslint-disable-next-line react-hooks/exhaustive-deps
  return useCallback(fn, deps);
};

/**
 * Detect if element is in viewport (for lazy rendering)
 * @param {Object} ref - Element ref
 * @param {Object} options - IntersectionObserver options
 */
export const useInView = (ref, options = {}) => {
  const [isInView, setIsInView] = useState(false);

  useEffect(() => {
    if (!ref.current) return;

    const observer = new IntersectionObserver(([entry]) => {
      setIsInView(entry.isIntersecting);
    }, options);

    observer.observe(ref.current);

    return () => {
      observer.disconnect();
    };
  }, [ref, options]);

  return isInView;
};

/**
 * Optimize state updates by batching
 */
export const useBatchedState = (initialState) => {
  const [state, setState] = useState(initialState);
  const pendingUpdates = useRef([]);
  const timeoutRef = useRef(null);

  const batchedSetState = useCallback((update) => {
    pendingUpdates.current.push(update);

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      setState(prevState => {
        return pendingUpdates.current.reduce((acc, fn) => {
          return typeof fn === 'function' ? fn(acc) : fn;
        }, prevState);
      });
      pendingUpdates.current = [];
    }, 0);
  }, []);

  return [state, batchedSetState];
};
