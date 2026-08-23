import { useNavigate } from "react-router-dom";

type Props = {
  title: string;
  status: string;
  description: string;
  link: string;
};

export default function OperationsDomainCard({
  title,
  status,
  description,
  link,
}: Props) {

  const navigate = useNavigate();

  return (
    <section className="operation-domain-card">

      <h3>{title}</h3>

      <strong>{status}</strong>

      <p>{description}</p>

      <button
        onClick={() => navigate(link)}
        className="dashboard-link"
      >
        Open Dashboard →
      </button>

    </section>
  );
}