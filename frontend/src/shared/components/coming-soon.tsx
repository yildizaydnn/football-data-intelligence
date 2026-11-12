import { Panel } from "./panel";

/** Geçici yer tutucu: bölüm içeriği sonraki adımlarda eklenecek. */
export function ComingSoon({ title }: { title: string }) {
  return (
    <Panel className="animate-fade-up py-16 text-center">
      <h2 className="font-display text-3xl font-extrabold uppercase">{title}</h2>
      <p className="mt-2 text-sm text-sage">Bu bölüm hazırlanıyor.</p>
    </Panel>
  );
}
