@'
type GovernanceNavigationButtonProps = {
  href?: string;
  label?: string;
};

export default function GovernanceNavigationButton({
  href = "/operations-center/governance",
  label = "AI Governance Center",
}: GovernanceNavigationButtonProps) {
  return (
    <a
      href={href}
      className="governance-navigation-button"
      aria-label={label}
    >
      <span className="governance-navigation-button__icon" aria-hidden="true">
        YETI
      </span>

      <span className="governance-navigation-button__label">
        {label}
      </span>
    </a>
  );
}
'@ | Set-Content ".\components\navigation\GovernanceNavigationButton.tsx" -Encoding utf8