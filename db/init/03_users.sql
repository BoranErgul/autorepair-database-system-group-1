-- Application users for the web interface (login and roles).
-- Passwords are stored as salted PBKDF2-SHA256 hashes, never as plain text.
-- Test accounts:  admin / admin123   (role: admin)
--                 staff / staff123   (role: staff)

CREATE TABLE APP_USER (
    UserID       INT          PRIMARY KEY,
    Username     VARCHAR(30)  NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    Role         VARCHAR(10)  NOT NULL CHECK (Role IN ('admin', 'staff'))
);

INSERT INTO APP_USER VALUES
  (1, 'admin', 'pbkdf2:sha256:1000000$TKpFnUH09qx0x6bk$60617b31e6e9c972ab6c68cc8048dd953676365a5b90379666642da63085618e', 'admin'),
  (2, 'staff', 'pbkdf2:sha256:1000000$KzjCxcL3iyA6VGMy$ded25b4f7257ee6d09158064cc80e25e74dbc41917a51272092c3bb8c1d9d7df', 'staff');
