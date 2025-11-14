'use client';

import { useEffect } from 'react';
import { checkAndApplyDebugParam } from '@/lib/debug';

/**
 * Client component to check for ?debug URL parameter and update debug mode
 * Rendered in root layout to work on all pages
 */
export default function DebugParamHandler() {
  useEffect(() => {
    checkAndApplyDebugParam();
  }, []);

  return null; // This component doesn't render anything
}
