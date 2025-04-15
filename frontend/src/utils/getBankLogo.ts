// src/utils/getBankLogo.ts
export const getBankLogo = (bank: string) => {
  switch (bank) {
    case "하나은행":
      return "/bank-logos/hana.png";
    case "우리은행":
      return "/bank-logos/woori.png";
    case "수협은행":
      return "/bank-logos/sh.png";
    case "신한은행":
      return "/bank-logos/shinhan.png";
    case "국민은행":
      return "/bank-logos/kb.png";
    case "수협중앙회":
      return "/bank-logos/shjoongang.png";
    default:
      return "/bank-logos/default.png";
  }
};
