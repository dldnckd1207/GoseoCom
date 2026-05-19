/**
 * [Golden File] 배럴 export 예시
 * 실제 위치: features/{domain}/index.ts
 *
 * 패턴 포인트:
 * - components + types만 export
 * - hooks와 api는 barrel에서 제외 (pages에서 직접 경로 import)
 */
export * from './components';
export * from './types';
