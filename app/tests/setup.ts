/**
 * Test setup - runs before all tests
 * Configures fake IndexedDB for testing
 */

import 'fake-indexeddb/auto';
import { vi } from 'vitest';

// Mock Date.now() for deterministic tests
let mockTime = 1700000000000;

export function setMockTime(timestamp: number) {
  mockTime = timestamp;
}

export function getMockTime() {
  return mockTime;
}

// Mock Date.now globally
vi.spyOn(Date, 'now').mockImplementation(() => mockTime);

// Mock Math.random for deterministic shuffle
let mockRandomValue = 0.5;
let mockRandomSequence: number[] = [];
let mockRandomIndex = 0;

export function setMockRandom(value: number) {
  mockRandomValue = value;
  mockRandomSequence = [];
  mockRandomIndex = 0;
}

export function setMockRandomSequence(sequence: number[]) {
  mockRandomSequence = sequence;
  mockRandomIndex = 0;
}

vi.spyOn(Math, 'random').mockImplementation(() => {
  if (mockRandomSequence.length > 0) {
    const value = mockRandomSequence[mockRandomIndex % mockRandomSequence.length];
    mockRandomIndex++;
    return value;
  }
  return mockRandomValue;
});
