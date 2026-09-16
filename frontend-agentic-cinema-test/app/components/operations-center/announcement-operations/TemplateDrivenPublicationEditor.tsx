"use client";

import { useEffect, useMemo, useState } from "react";
import {
  createTemplateDraft,
  getEditorTemplates,
  previewTemplate,
  type TemplateEditorOption,
} from "@/app/lib/api/announcementTemplateEditor";

export default function TemplateDrivenPublicationEditor() {
  const [templates, setTemplates] = useState<TemplateEditorOption[]>([]);
  const [templateId, setTemplateId] = useState("");
  const [values, setValues] = useState<Record<string, string>>({});
  const [title, setTitle] = useState("");
  const [preview, setPreview] = useState("");
  const [loadingTemplates, setLoadingTemplates] = useState(true);
  const [previewing, setPreviewing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const selectedTemplate = useMemo(
    () => templates.find((item) => item.template_id === templateId) ?? null,
    [templateId, templates],
  );

  useEffect(() => {
    getEditorTemplates()
      .then((items) => {
        setTemplates(items);
        if (items.length > 0) {
          setTemplateId(items[0].template_id);
        }
      })
      .catch((reason: unknown) => {
        setError(
          reason instanceof Error
            ? reason.message
            : "Announcement types could not be loaded.",
        );
      })
      .finally(() => setLoadingTemplates(false));
  }, []);

  useEffect(() => {
    if (!selectedTemplate) {
      setValues({});
      setPreview("");
      return;
    }

    const nextValues: Record<string, string> = {};
    for (const field of selectedTemplate.fields) {
      nextValues[field.name] = "";
    }

    setValues(nextValues);
    setPreview("");
    setError(null);
  }, [selectedTemplate]);

  const requiredFieldsMissing = selectedTemplate
    ? selectedTemplate.fields.some(
        (field) => field.required && !values[field.name]?.trim(),
      )
    : true;

  const canPreview =
    Boolean(selectedTemplate) &&
    Boolean(title.trim()) &&
    !requiredFieldsMissing;

  function updateValue(name: string, value: string) {
    setValues((current) => ({ ...current, [name]: value }));
    setMessage(null);
  }

  async function handlePreview() {
    if (!selectedTemplate || !canPreview) {
      return;
    }

    setPreviewing(true);
    setError(null);
    setMessage(null);

    try {
      const result = await previewTemplate({
        templateId: selectedTemplate.template_id,
        templateVersion: selectedTemplate.version,
        values,
      });
      setPreview(result.content);
    } catch (reason: unknown) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Preview could not be generated.",
      );
    } finally {
      setPreviewing(false);
    }
  }

  async function handleSaveDraft() {
    if (!selectedTemplate || !canPreview) {
      return;
    }

    setSaving(true);
    setError(null);
    setMessage(null);

    try {
      const result = await createTemplateDraft({
        templateId: selectedTemplate.template_id,
        templateVersion: selectedTemplate.version,
        title: title.trim(),
        values,
      });

      setMessage(
        `Draft ${result.id} saved from ${result.template_id} v${result.template_version}.`,
      );
    } catch (reason: unknown) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The draft could not be saved.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="min-h-full p-6 lg:p-10">
      <div className="mb-8">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-fuchsia-300">
          Announcement Operations
        </p>
        <h1 className="mt-2 text-3xl font-bold text-white">
          Create publication
        </h1>
        <p className="mt-2 text-sm text-slate-400">
          Select an approved announcement type, complete its controlled fields,
          preview it, and save a draft.
        </p>
      </div>

      {error && (
        <div
          role="alert"
          className="mb-6 rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-200"
        >
          {error}
        </div>
      )}

      {message && (
        <div className="mb-6 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm text-emerald-200">
          {message}
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6">
          <h2 className="font-semibold text-white">Publication content</h2>

          <label
            htmlFor="announcement-type"
            className="mt-5 block text-xs font-semibold uppercase tracking-wider text-slate-500"
          >
            Announcement type
          </label>

          <select
            id="announcement-type"
            aria-label="Announcement type"
            value={templateId}
            disabled={loadingTemplates || templates.length === 0}
            onChange={(event) => setTemplateId(event.target.value)}
            className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none focus:border-fuchsia-500 disabled:opacity-50"
          >
            {loadingTemplates && (
              <option value="">Loading announcement types…</option>
            )}
            {!loadingTemplates && templates.length === 0 && (
              <option value="">No announcement types available</option>
            )}
            {templates.map((template) => (
              <option key={template.template_id} value={template.template_id}>
                {template.name}
              </option>
            ))}
          </select>

          {selectedTemplate && (
            <div className="mt-3 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full bg-fuchsia-500/10 px-2.5 py-1 text-xs font-semibold text-fuchsia-300">
                  {selectedTemplate.category}
                </span>
                <span className="text-xs text-slate-500">
                  Approved version {selectedTemplate.version}
                </span>
              </div>
              <p className="mt-2 text-sm text-slate-400">
                {selectedTemplate.description}
              </p>
            </div>
          )}

          <label
            htmlFor="announcement-title"
            className="mt-5 block text-xs font-semibold uppercase tracking-wider text-slate-500"
          >
            Publication title
          </label>
          <input
            id="announcement-title"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none focus:border-fuchsia-500"
            placeholder="Announcement title"
          />

          {selectedTemplate?.fields.map((field) => (
            <div key={field.name}>
              <label
                htmlFor={`template-field-${field.name}`}
                className="mt-5 block text-xs font-semibold uppercase tracking-wider text-slate-500"
              >
                {field.label}
                {field.required && (
                  <span className="ml-1 text-fuchsia-300">*</span>
                )}
              </label>

              {field.multiline ? (
                <textarea
                  id={`template-field-${field.name}`}
                  value={values[field.name] ?? ""}
                  onChange={(event) =>
                    updateValue(field.name, event.target.value)
                  }
                  rows={5}
                  className="mt-2 w-full resize-y rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none focus:border-fuchsia-500"
                />
              ) : (
                <input
                  id={`template-field-${field.name}`}
                  value={values[field.name] ?? ""}
                  onChange={(event) =>
                    updateValue(field.name, event.target.value)
                  }
                  className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none focus:border-fuchsia-500"
                />
              )}
            </div>
          ))}

          {selectedTemplate && requiredFieldsMissing && (
            <p className="mt-4 text-xs text-amber-300">
              Complete all required fields before previewing or saving.
            </p>
          )}

          <div className="mt-5 flex flex-wrap gap-3">
            <button
              type="button"
              disabled={!canPreview || previewing}
              onClick={handlePreview}
              className="rounded-xl border border-fuchsia-500/50 px-5 py-3 text-sm font-semibold text-fuchsia-200 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {previewing ? "Previewing…" : "Preview"}
            </button>

            <button
              type="button"
              disabled={!canPreview || saving}
              onClick={handleSaveDraft}
              className="rounded-xl bg-fuchsia-500 px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
            >
              {saving ? "Saving…" : "Save draft"}
            </button>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6">
          <p className="text-xs font-bold uppercase tracking-wider text-fuchsia-300">
            Preview
          </p>

          <div className="mt-4 rounded-2xl border border-slate-800 bg-[#050816] p-6">
            <p className="text-xs uppercase tracking-wider text-slate-500">
              EasyChatBot Academy
            </p>
            <h2 className="mt-3 text-2xl font-bold text-white">
              {title || "Announcement title"}
            </h2>
            <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-slate-300">
              {preview ||
                "Complete the selected announcement type and choose Preview to see the rendered announcement."}
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
