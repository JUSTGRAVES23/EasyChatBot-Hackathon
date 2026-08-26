import OperationsCenterShell from "@/app/components/operations-center/OperationsCenterShell";
import TemplateDrivenPublicationEditor from "@/app/components/operations-center/announcement-operations/TemplateDrivenPublicationEditor";

export default function CreateAnnouncementPublicationPage() {
  return (
    <OperationsCenterShell>
      <TemplateDrivenPublicationEditor />
    </OperationsCenterShell>
  );
}
