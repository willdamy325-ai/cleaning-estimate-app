import type { Service } from "@/domain/types";

/**
 * 料金カタログ。将来はデータベースや管理画面から取得する想定。
 * ここでは単一のソースとして定義し、UI と計算ロジックが同じ値を参照する。
 */
export const SERVICE_CATALOG: Service[] = [
  {
    id: "standard-ac",
    name: "通常エアコン",
    description: "フィルター・フィンの徹底洗浄",
    unitLabel: "台",
    price: 7000,
  },
  {
    id: "auto-clean-ac",
    name: "お掃除機能付きエアコン",
    description: "内部ユニットに対応した分解洗浄",
    unitLabel: "台",
    price: 12000,
  },
  {
    id: "bathroom",
    name: "浴室",
    description: "浴槽・壁・床・排水口の清掃",
    unitLabel: "箇所",
    price: 12000,
  },
  {
    id: "washbasin",
    name: "洗面所",
    description: "ボウル・水栓・鏡まわりの清掃",
    unitLabel: "箇所",
    price: 6000,
  },
  {
    id: "range-hood",
    name: "レンジフード",
    description: "ファン・フィルターの油汚れ洗浄",
    unitLabel: "台",
    price: 12000,
  },
  {
    id: "kitchen",
    name: "キッチン",
    description: "コンロ・シンク周辺の油汚れ清掃",
    unitLabel: "箇所",
    price: 12000,
  },
  {
    id: "toilet",
    name: "トイレ",
    description: "便器・床・壁の除菌清掃",
    unitLabel: "箇所",
    price: 6000,
  },
  {
    id: "washing-machine",
    name: "洗濯機",
    description: "槽内のカビ・汚れ洗浄",
    unitLabel: "台",
    price: 20000,
  },
];

export function getServiceById(id: string): Service | undefined {
  return SERVICE_CATALOG.find((service) => service.id === id);
}
