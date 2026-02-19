DELIMITER $$

DROP PROCEDURE IF EXISTS add_user $$

CREATE PROCEDURE add_user(
    IN p_tenant_id INT,
    IN p_username VARCHAR(50),
    IN p_password_hash VARCHAR(255),
    IN p_email VARCHAR(100),
    IN p_role VARCHAR(20)
)
BEGIN
    -- Create a tenant for this user (User IS Tenant model)
    INSERT INTO tenants (name) VALUES (p_username);
    SET @new_tenant_id = LAST_INSERT_ID();

    INSERT INTO users (tenant_id, username, password_hash, email, role)
    VALUES (@new_tenant_id, p_username, p_password_hash, p_email, p_role);
    
    SELECT LAST_INSERT_ID();
END $$

DROP PROCEDURE IF EXISTS delete_user $$

CREATE PROCEDURE delete_user(
    IN p_tenant_id INT,
    IN p_user_id INT
)
BEGIN
    DELETE FROM users WHERE user_id = p_user_id AND tenant_id = p_tenant_id;
END $$

DELIMITER ;