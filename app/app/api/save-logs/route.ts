/**
 * API route to save logs to file system (development only)
 * POST /api/save-logs
 */

import { NextRequest, NextResponse } from 'next/server';
import { writeFile, mkdir } from 'fs/promises';
import { join } from 'path';

export async function POST(request: NextRequest) {
  // Only allow in development
  if (process.env.NODE_ENV !== 'development') {
    return NextResponse.json(
      { error: 'Only available in development' },
      { status: 403 }
    );
  }

  try {
    const body = await request.json();
    const { logs } = body;

    if (!logs || !Array.isArray(logs)) {
      return NextResponse.json(
        { error: 'Invalid logs format' },
        { status: 400 }
      );
    }

    // Create logs directory if it doesn't exist
    const logsDir = join(process.cwd(), 'logs');
    await mkdir(logsDir, { recursive: true });

    // Format logs as text
    const text = logs.map((entry: any) => {
      const date = new Date(entry.timestamp).toISOString();
      const dataStr = entry.data ? `\n  ${JSON.stringify(entry.data, null, 2)}` : '';
      return `[${date}] [${entry.level.toUpperCase()}] [${entry.tag}] ${entry.message}${dataStr}`;
    }).join('\n\n');

    // Write to file with timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `hanzi-flow-${timestamp}.log`;
    const filepath = join(logsDir, filename);

    await writeFile(filepath, text, 'utf8');

    return NextResponse.json({
      success: true,
      filename,
      count: logs.length
    });
  } catch (error) {
    console.error('Failed to save logs:', error);
    return NextResponse.json(
      { error: 'Failed to save logs' },
      { status: 500 }
    );
  }
}
