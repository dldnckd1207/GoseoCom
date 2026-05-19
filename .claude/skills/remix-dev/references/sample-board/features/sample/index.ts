/**
 * [Golden File] 배럴 export 예시
 * 실제 위치: features/{domain}/index.ts
 *
 * 패턴 포인트:
 * - types, api, ui만 export (hooks는 직접 경로로 import)
 * - named export만 사용 (default export 금지)
 */
export * from './types';
export * as sampleApi from './api';
export { SampleSearchForm } from './ui/SampleSearchForm';
export { SampleTable } from './ui/SampleTable';
