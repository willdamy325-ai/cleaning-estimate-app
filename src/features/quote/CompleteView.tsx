"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { QuoteReceipt } from "@/components/complete/QuoteReceipt";
import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import type { QuoteRequest } from "@/domain/types";
import {
  getLastQuoteId,
  LocalQuoteRepository,
} from "@/infrastructure/repositories/localQuoteRepository";

export function CompleteView() {
  const [quote, setQuote] = useState<QuoteRequest | null | undefined>(undefined);

  useEffect(() => {
    let active = true;

    async function loadQuote() {
      const id = getLastQuoteId();
      const repository = new LocalQuoteRepository();
      const result = id ? await repository.findById(id) : await Promise.resolve(null);
      if (active) {
        setQuote(result);
      }
    }

    void loadQuote();
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="min-h-dvh bg-mist text-ink">
      <Header />
      <main className="mx-auto max-w-content px-5 py-8 sm:py-12">
        {quote === undefined ? (
          <p className="rounded-3xl bg-paper px-5 py-10 text-center text-clay shadow-card">
            見積内容を読み込んでいます...
          </p>
        ) : quote === null ? (
          <section className="rounded-[28px] border border-gold-soft bg-paper px-5 py-12 text-center shadow-card">
            <h1 className="font-serif text-2xl text-pine-deep">見積データが見つかりません</h1>
            <p className="mt-3 text-sm text-clay">トップページからサービスを選択し、見積をご依頼ください。</p>
            <Link
              href="/"
              className="mt-8 inline-flex h-12 items-center rounded-full bg-pine px-6 text-sm text-paper"
            >
              見積に戻る
            </Link>
          </section>
        ) : (
          <div className="space-y-6">
            <QuoteReceipt quote={quote} />
            <p className="text-center text-sm leading-7 text-clay">
              ご依頼内容を保存しました。
              <br />
              担当者が内容を確認し、入力いただいた連絡先へ正式なお見積と日程をご案内します。
            </p>
            <div className="flex justify-center">
              <Link
                href="/"
                className="inline-flex h-12 items-center rounded-full border border-pine/30 bg-paper px-6 text-sm text-pine hover:bg-gold-pale"
              >
                別の見積を作成する
              </Link>
            </div>
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
}
