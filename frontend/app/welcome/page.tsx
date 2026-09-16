export default function WelcomePage() {
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "32px",
        boxSizing: "border-box",
      }}
    >
      <section
        style={{
          width: "100%",
          maxWidth: "520px",
          textAlign: "center",
        }}
      >
        <h1>Welcome to EasyChatBot Academy</h1>

        <p>
          Your French learning environment starts here.
        </p>

        <p>
          Create your account to access the Academy.
        </p>

        <div
          style={{
            display: "flex",
            gap: "12px",
            justifyContent: "center",
            marginTop: "24px",
            flexWrap: "wrap",
          }}
        >
          <a href="/operations-center/governance">
            Operations Center
          </a>
        </div>
      </section>
    </main>
  );
}
