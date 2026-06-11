export interface PageData<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}
