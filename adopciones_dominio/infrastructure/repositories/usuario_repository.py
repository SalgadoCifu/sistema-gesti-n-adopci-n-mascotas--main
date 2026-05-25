from sqlalchemy import text


class UsuarioRepository:

    def __init__(self, engine):
        self.engine = engine

    def obtener_por_cedula(self, cedula: str):

        query = text("""
            SELECT
                cedula,
                correo,
                nombre,
                tipouser
            FROM usuarios
            WHERE cedula = :cedula
        """)

        try:
            with self.engine.connect() as conn:

                result = conn.execute(query, {
                    "cedula": cedula
                })

                row = result.fetchone()

                if row:
                    return dict(row._mapping)

                return None

        except Exception as e:
            raise Exception(f"Error obteniendo usuario: {e}")