from sqlalchemy import create_engine, text

engine = create_engine('postgresql+psycopg2://hlas:hlas@localhost:5433/hlas', future=True)

password_hash = 'scrypt:32768:8:1$1J7UuF8zEsZ0OTe8$54340c71e82ddaa0d110029cb9913e08aaeb176d001998e02aa4c453eb4273be81da556090129996d21e3bf31a3ddcd2da7cbade20af49610db2752fc5406e79'

with engine.begin() as conn:
    conn.execute(text("UPDATE members SET password = :password WHERE username = 'admin'"), {'password': password_hash})
    result = conn.execute(text("SELECT password FROM members WHERE username = 'admin'"))
    print("Stored hash:", result.scalar())
