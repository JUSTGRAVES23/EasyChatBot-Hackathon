SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'auth_password_reset_tokens'
ORDER BY ordinal_position;

SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'auth_password_reset_tokens'
ORDER BY indexname;

SELECT
    conname,
    pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'auth_password_reset_tokens'::regclass
ORDER BY conname;
