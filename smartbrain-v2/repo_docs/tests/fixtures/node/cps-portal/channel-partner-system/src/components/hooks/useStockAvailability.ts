import { get, post } from '@/utils/api';

export interface StockQuery {
  productCatalogId: string;
  quantity?: number;
}

export const checkBulkStockAvailability = async (ids: string[]) => {
  const response: any = await (post as any)('/v1/inventory/list', {
    and: [{ field: 'productCatalogId', operation: 'in', value: ids }],
  });
  return response?.data;
};

export const getStock = async (id: string) => get<StockQuery>(`/v1/inventory/${id}`);
