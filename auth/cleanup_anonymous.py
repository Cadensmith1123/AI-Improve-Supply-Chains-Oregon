import os
from dotenv import load_dotenv
from db.functions.connect import get_auth_db, get_db

load_dotenv()
ANON_MAX_AGE_SECONDS = int(os.getenv("ANON_MAX_AGE_SECONDS"))


def cleanup():
    auth_conn = get_auth_db()
    if auth_conn is None:
        print("Cleanup failed: could not connect to auth DB")
        return

    deleted_tenant_ids = []
    auth_cur = None
    try:
        auth_cur = auth_conn.cursor()

        auth_cur.execute("SELECT COUNT(*) FROM users WHERE role = 'Anonymous'")
        before = auth_cur.fetchone()[0]

        auth_cur.callproc("clean_anon_users", [ANON_MAX_AGE_SECONDS])
        for result in auth_cur.stored_results():
            deleted_tenant_ids.extend(row[0] for row in result.fetchall())
        auth_conn.commit()

        auth_cur.execute("SELECT COUNT(*) FROM users WHERE role = 'Anonymous'")
        after = auth_cur.fetchone()[0]

        print(f"Auth cleanup: removed {before - after} anonymous users (was {before}, now {after}, max age {ANON_MAX_AGE_SECONDS}s)")
    finally:
        if auth_cur:
            auth_cur.close()
        auth_conn.close()

    if not deleted_tenant_ids:
        return

    # Cascade cleanup into local_food_db
    main_conn = get_db()
    if main_conn is None:
        print(f"Warning: auth cleanup ran but could not connect to main DB. orphaned tenant_ids: {deleted_tenant_ids}")
        return

    main_cur = None
    try:
        main_cur = main_conn.cursor()
        main_cur.callproc("delete_tenant_data", [",".join(map(str, deleted_tenant_ids))])
        main_conn.commit()
        print(f"Main cleanup: removed data for {len(deleted_tenant_ids)} tenants")
    finally:
        if main_cur:
            main_cur.close()
        main_conn.close()


if __name__ == "__main__":
    cleanup()
