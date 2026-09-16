"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { getQuoteService } from "@/application/quoteService";
import { CustomerForm } from "@/components/customer/CustomerForm";
import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import { QuoteSummary } from "@/components/quote/QuoteSummary";
import { ServiceList } from "@/components/quote/ServiceList";
import { StepIndicator } from "@/components/quote/StepIndicator";
import { StickyQuoteBar } from "@/components/quote/StickyQuoteBar";
import {
  EMPTY_CUSTOMER,
  hasCustomerErrors,
  type CustomerErrors,
  type CustomerField,
  validateCustomer,
} from "@/domain/customer";
import { calculateQuote, changeQuantity, createEmptyQuantities } from "@/domain/quote";
import type { CustomerInfo, QuantityMap, ServiceId } from "@/domain/types";
import { cn } from "@/lib/cn";

export function QuoteFlow() {
  const router = useRouter();
  const [step, setStep] = useState<1 | 2>(1);
  const [quantities, setQuantities] = useState<QuantityMap>(createEmptyQuantities);
  const [customer, setCustomer] = useState<CustomerInfo>(EMPTY_CUSTOMER);
  const [errors, setErrors] = useState<CustomerErrors>({});
  const [submitError, setSubmitError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const quote = useMemo(() => calculateQuote(quantities), [quantities]);
  const hasSelection = quote.lines.length > 0;

  function handleQuantityChange(serviceId: ServiceId, value: number) {
    setQuantities((current) => changeQuantity(current, serviceId, value));
  }

  function handleCustomerChange(field: CustomerField, value: string) {
    setCustomer((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  }

  function goToCustomerStep() {
    if (!hasSelection) {
      return;
    }
    setStep(2);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function handleSubmit() {
    const nextErrors = validateCustomer(customer);
    setErrors(nextErrors);
    setSubmitError("");

    if (!hasSelection) {
      setSubmitError("サービスを1つ以上選択してください");
      setStep(1);
      return;
    }

    if (hasCustomerErrors(nextErrors)) {
      setSubmitError("入力内容をご確認ください");
      return;
    }

    setSubmitting(true);
    try {
      await getQuoteService().submit(quantities, customer);
      router.push("/complete");
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "送信に失敗しました");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-dvh bg-mist text-ink">
      <Header />
      <main className="mx-auto max-w-content px-5 pb-32 pt-8 lg:pb-16">
        <section className="overflow-hidden rounded-[28px] border border-gold-soft bg-paper px-5 py-8 shadow-card sm:px-10">
          <p className="text-[11px] tracking-[0.32em] text-gold">PROFESSIONAL HOUSE CLEANING</p>
          <h1 className="mt-3 font-serif text-[1.7rem] leading-snug text-pine-deep sm:text-4xl">
            その場で料金がわかる、
            <br className="hidden sm:block" />
            清掃サービス見積もり
          </h1>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-clay sm:text-base">
            必要なサービスを選ぶと、数量と合計金額がすぐに表示されます。内容をご確認のうえ、お客様情報を入力して見積をご依頼ください。
          </p>
        </section>

        <div className="mt-8">
          <StepIndicator current={step} />
        </div>

        {step === 1 ? (
          <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
            <ServiceList quantities={quantities} onQuantityChange={handleQuantityChange} />
            <aside className="hidden lg:block">
              <div className="sticky top-24 space-y-4">
                <QuoteSummary quote={quote} />
                <button
                  type="button"
                  onClick={goToCustomerStep}
                  disabled={!hasSelection}
                  className={cn(
                    "h-12 w-full rounded-full text-sm tracking-wide transition",
                    hasSelection
                      ? "bg-pine text-paper hover:bg-pine-deep"
                      : "cursor-not-allowed bg-gold-soft text-clay",
                  )}
                >
                  お客様情報の入力へ
                </button>
              </div>
            </aside>
          </div>
        ) : (
          <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
            <div className="space-y-4">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="text-sm text-pine underline-offset-4 hover:underline"
              >
                ← サービス選択に戻る
              </button>
              <CustomerForm value={customer} errors={errors} onChange={handleCustomerChange} />
              {submitError ? (
                <p className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
                  {submitError}
                </p>
              ) : null}
              <div className="hidden gap-3 lg:flex">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="h-12 flex-1 rounded-full border border-pine/30 bg-paper text-sm text-pine hover:bg-gold-pale"
                >
                  サービス選択に戻る
                </button>
                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="h-12 flex-[1.4] rounded-full bg-pine text-sm text-paper hover:bg-pine-deep disabled:opacity-60"
                >
                  {submitting ? "送信中..." : "見積を依頼する"}
                </button>
              </div>
            </div>
            <aside className="space-y-4">
              <QuoteSummary quote={quote} />
              <button
                type="button"
                onClick={() => setStep(1)}
                className="hidden w-full text-sm text-pine underline-offset-4 hover:underline lg:block"
              >
                数量を変更する
              </button>
            </aside>
          </div>
        )}
      </main>
      <Footer />
      <StickyQuoteBar
        total={quote.total}
        disabled={step === 1 ? !hasSelection : submitting}
        label={step === 1 ? "お客様情報へ" : submitting ? "送信中..." : "見積を依頼する"}
        onAction={step === 1 ? goToCustomerStep : handleSubmit}
      />
    </div>
  );
}
