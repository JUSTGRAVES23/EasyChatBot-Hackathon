export interface TemplateEditorField {
  name: string;
  required: boolean;
  label: string;
  multiline: boolean;
}

export interface TemplateEditorOption {
  template_id: string;
  name: string;
  category: string;
  description: string;
  version: number;
  publication_type: string;
  fields: TemplateEditorField[];
}

export interface TemplateEditorPreview {
  template_id: string;
  template_version: number;
  publication_type: string;
  content: string;
}

export interface CreatedDraftPublication {
  id: string;
  title: string;
  content: string;
  template_id: string;
  template_version: number;
  publication_type: string;
  status: string;
  created_at: string | null;
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = `Announcement template API returned ${response.status}.`;

    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) {
        detail = body.detail;
      }
    } catch {
      // Preserve the stable HTTP error for non-JSON responses.
    }

    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

export function getEditorTemplates(): Promise<TemplateEditorOption[]> {
  return request<TemplateEditorOption[]>(
    "/api/announcement-operations/template-editor/templates",
  );
}

export function previewTemplate(input: {
  templateId: string;
  templateVersion: number;
  values: Record<string, string>;
}): Promise<TemplateEditorPreview> {
  return request<TemplateEditorPreview>(
    "/api/announcement-operations/template-editor/preview",
    {
      method: "POST",
      body: JSON.stringify({
        template_id: input.templateId,
        template_version: input.templateVersion,
        values: input.values,
      }),
    },
  );
}

export function createTemplateDraft(input: {
  templateId: string;
  templateVersion: number;
  title: string;
  values: Record<string, string>;
}): Promise<CreatedDraftPublication> {
  return request<CreatedDraftPublication>(
    "/api/announcement-operations/template-editor/drafts",
    {
      method: "POST",
      body: JSON.stringify({
        template_id: input.templateId,
        template_version: input.templateVersion,
        title: input.title,
        values: input.values,
      }),
    },
  );
}
