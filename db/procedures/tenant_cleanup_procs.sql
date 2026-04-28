DELIMITER $$

DROP PROCEDURE IF EXISTS delete_tenant_data $$
CREATE PROCEDURE delete_tenant_data(IN p_tenant_ids VARCHAR(4000))
BEGIN
    DELETE FROM manifest_items   WHERE FIND_IN_SET(tenant_id, p_tenant_ids);
    DELETE FROM scenarios        WHERE FIND_IN_SET(tenant_id, p_tenant_ids);
    DELETE FROM routes           WHERE FIND_IN_SET(tenant_id, p_tenant_ids);
    DELETE FROM supply           WHERE FIND_IN_SET(tenant_id, p_tenant_ids);
    DELETE FROM demand           WHERE FIND_IN_SET(tenant_id, p_tenant_ids);
    DELETE FROM entities         WHERE FIND_IN_SET(tenant_id, p_tenant_ids);
    DELETE FROM drivers          WHERE FIND_IN_SET(tenant_id, p_tenant_ids);
    DELETE FROM vehicles         WHERE FIND_IN_SET(tenant_id, p_tenant_ids);
    DELETE FROM products_master  WHERE FIND_IN_SET(tenant_id, p_tenant_ids);
    DELETE FROM locations        WHERE FIND_IN_SET(tenant_id, p_tenant_ids);
END $$

DELIMITER ;