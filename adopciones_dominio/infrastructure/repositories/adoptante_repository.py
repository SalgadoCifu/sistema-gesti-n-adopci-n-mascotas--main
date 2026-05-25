from sqlalchemy import text


class AdoptanteRepository:

    def __init__(self, engine):
        self.engine = engine

    def obtener_por_cedula(self, cedula: str):

        query = text("""
            SELECT
                cedula,
                direccion,
                telefono,
                codlocalidad
            FROM adoptantes
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
            raise Exception(f"Error obteniendo adoptante: {e}")

    def crear_adoptante(
        self,
        cedula,
        direccion,
        telefono,
        codlocalidad
    ):

        query = text("""
            INSERT INTO adoptantes (
                cedula,
                direccion,
                telefono,
                codlocalidad
            )
            VALUES (
                :cedula,
                :direccion,
                :telefono,
                :codlocalidad
            )
        """)

        try:
            with self.engine.begin() as conn:

                conn.execute(query, {
                    "cedula": cedula,
                    "direccion": direccion,
                    "telefono": telefono,
                    "codlocalidad": codlocalidad
                })

        except Exception as e:
            raise Exception(f"Error creando adoptante: {e}")