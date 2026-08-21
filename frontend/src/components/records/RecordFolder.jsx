import { Link } from "react-router-dom";
import { FileText, Lock } from "lucide-react";
import { formatDateTime } from "../../lib/format";

export function RecordFolder({ record, href }) {
  const docs = record.documents || [];
  const body = (
    <>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.14em] text-muted">
            {record.hospital_name || "Hospital"}
          </p>
          <h3 className="mt-1 font-display text-lg text-ink">
            {record.diagnosis}
          </h3>
        </div>
        <Lock className="h-4 w-4 shrink-0 text-teal-700" aria-label="Immutable" />
      </div>
      {record.chief_complaint ? (
        <p className="mt-2 text-sm text-muted line-clamp-2">
          {record.chief_complaint}
        </p>
      ) : null}
      <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-muted">
        <span>{record.doctor_name}</span>
        <span>·</span>
        <span>{formatDateTime(record.created_at)}</span>
        <span className="inline-flex items-center gap-1">
          <FileText className="h-3.5 w-3.5" />
          {docs.length} file{docs.length === 1 ? "" : "s"}
        </span>
      </div>
    </>
  );

  const className =
    "block rounded-2xl border border-line bg-white p-5 transition hover:border-teal-400 hover:shadow-md hover:shadow-teal-900/5";

  if (href) {
    return (
      <Link to={href} className={className}>
        {body}
      </Link>
    );
  }
  return <div className={className}>{body}</div>;
}

export function RecordDetailView({ record, note }) {
  const docs = record.documents || [];
  return (
    <article className="space-y-6">
      <div className="rounded-2xl border border-line bg-white p-5 sm:p-7">
        <p className="text-xs uppercase tracking-[0.16em] text-teal-700">
          Encounter folder · immutable
        </p>
        <h1 className="mt-2 font-display text-2xl sm:text-3xl">{record.diagnosis}</h1>
        <p className="mt-3 text-sm text-muted">
          {record.hospital_name} · {record.doctor_name} ·{" "}
          {formatDateTime(record.created_at)}
        </p>
        {note ? <p className="mt-3 text-xs text-teal-800">{note}</p> : null}
      </div>

      {record.chief_complaint ? (
        <section>
          <h2 className="font-display text-lg">Chief complaint</h2>
          <p className="mt-2 whitespace-pre-wrap text-sm text-ink/80">
            {record.chief_complaint}
          </p>
        </section>
      ) : null}

      {record.doctor_notes ? (
        <section>
          <h2 className="font-display text-lg">Doctor notes</h2>
          <p className="mt-2 whitespace-pre-wrap text-sm text-ink/80">
            {record.doctor_notes}
          </p>
        </section>
      ) : null}

      <section>
        <h2 className="font-display text-lg">Filed documents</h2>
        {docs.length === 0 ? (
          <p className="mt-2 text-sm text-muted">No files in this folder.</p>
        ) : (
          <ul className="mt-3 space-y-2">
            {docs.map((doc) => (
              <li key={doc.id}>
                <a
                  href={doc.doc_url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-3 rounded-xl border border-line bg-white px-4 py-3 text-sm hover:border-teal-400"
                >
                  <FileText className="h-4 w-4 text-teal-700" />
                  <span className="flex-1 font-medium">{doc.title}</span>
                  <span className="text-xs text-muted">Open</span>
                </a>
              </li>
            ))}
          </ul>
        )}
      </section>
    </article>
  );
}
