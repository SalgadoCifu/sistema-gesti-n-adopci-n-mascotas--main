-- ============================================================================
-- SISTEMA DE GESTIÓN DE ADOPCIÓN DE MASCOTAS
-- Script DDL SQL idempotente para Supabase (Database + Auth)
-- ============================================================================

-- Habilitar extensión UUID si no está activa
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------------------
-- 1. TABLAS DE CATÁLOGO
-- ----------------------------------------------------------------------------

-- Tipos de Mascotas
CREATE TABLE IF NOT EXISTS public.tipomascotas (
    codtipomascota INTEGER PRIMARY KEY,
    nomtipomascota VARCHAR(50) NOT NULL
);

-- Localidades de Bogotá
CREATE TABLE IF NOT EXISTS public.localidades (
    codlocalidad INTEGER PRIMARY KEY,
    nomlocalidad VARCHAR(100) NOT NULL
);

-- ----------------------------------------------------------------------------
-- 2. TABLAS PRINCIPALES (Usuarios y Adoptantes)
-- ----------------------------------------------------------------------------

-- Usuarios del sistema (vinculados opcionalmente con auth.users de Supabase)
CREATE TABLE IF NOT EXISTS public.usuarios (
    cedula VARCHAR(20) PRIMARY KEY,
    correo VARCHAR(255) NOT NULL UNIQUE,
    nombre VARCHAR(150) NOT NULL,
    tipouser VARCHAR(50) NOT NULL DEFAULT 'adoptante',
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- Adoptantes (detalles del adoptante vinculados con usuarios)
CREATE TABLE IF NOT EXISTS public.adoptantes (
    cedula VARCHAR(20) PRIMARY KEY REFERENCES public.usuarios(cedula) ON DELETE CASCADE,
    direccion VARCHAR(255),
    telefono VARCHAR(50),
    codlocalidad INTEGER REFERENCES public.localidades(codlocalidad) ON DELETE SET NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- ----------------------------------------------------------------------------
-- 3. TABLA MASCOTAS
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.mascotas (
    codmascota BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    especie VARCHAR(50) NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'disponible' 
        CHECK (estado IN ('disponible', 'en_proceso', 'adoptada', 'no disponible')),
    fechaingreso TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    codtipomascota INTEGER REFERENCES public.tipomascotas(codtipomascota) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- ----------------------------------------------------------------------------
-- 4. TABLA SOLICITUDES DE ADOPCIÓN
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.solicitudes (
    codsolicitud BIGSERIAL PRIMARY KEY,
    cedula VARCHAR(20) NOT NULL REFERENCES public.adoptantes(cedula) ON DELETE CASCADE,
    codmascota BIGINT NOT NULL REFERENCES public.mascotas(codmascota) ON DELETE CASCADE,
    fechasolicitud TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    estado VARCHAR(30) NOT NULL DEFAULT 'pendiente' 
        CHECK (estado IN ('pendiente', 'en_revision', 'en_proceso', 'aprobada', 'rechazada')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- ----------------------------------------------------------------------------
-- 5. TABLA ADOPCIONES FINALIZADAS
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.adopciones (
    codadopcion BIGSERIAL PRIMARY KEY,
    cedula VARCHAR(20) NOT NULL REFERENCES public.adoptantes(cedula) ON DELETE CASCADE,
    codmascota BIGINT NOT NULL REFERENCES public.mascotas(codmascota) ON DELETE CASCADE,
    fechaadopcion TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- ----------------------------------------------------------------------------
-- 6. ÍNDICES DE RENDIMIENTO
-- ----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_usuarios_user_id ON public.usuarios(user_id);
CREATE INDEX IF NOT EXISTS idx_adoptantes_user_id ON public.adoptantes(user_id);
CREATE INDEX IF NOT EXISTS idx_mascotas_estado ON public.mascotas(estado);
CREATE INDEX IF NOT EXISTS idx_solicitudes_cedula ON public.solicitudes(cedula);
CREATE INDEX IF NOT EXISTS idx_solicitudes_codmascota ON public.solicitudes(codmascota);
CREATE INDEX IF NOT EXISTS idx_solicitudes_estado ON public.solicitudes(estado);
CREATE INDEX IF NOT EXISTS idx_adopciones_cedula ON public.adopciones(cedula);

-- ----------------------------------------------------------------------------
-- 7. INTEGRACIÓN CON Supabase Auth (auth.users -> usuarios / adoptantes)
-- ----------------------------------------------------------------------------

-- Trigger function para sincronizar automáticamente el user_id de auth.users
CREATE OR REPLACE FUNCTION public.handle_new_auth_user()
RETURNS TRIGGER 
LANGUAGE plpgsql 
SECURITY DEFINER 
SET search_path = public
AS $$
DECLARE
    v_cedula VARCHAR(20);
    v_nombre VARCHAR(150);
BEGIN
    v_cedula := (NEW.raw_user_meta_data->>'cedula');
    v_nombre := COALESCE(NEW.raw_user_meta_data->>'nombre', split_part(NEW.email, '@', 1));

    IF v_cedula IS NOT NULL AND trim(v_cedula) <> '' THEN
        -- Insertar o actualizar usuario asociando el user_id
        INSERT INTO public.usuarios (cedula, correo, nombre, tipouser, user_id)
        VALUES (v_cedula, NEW.email, v_nombre, 'adoptante', NEW.id)
        ON CONFLICT (cedula) DO UPDATE 
        SET user_id = EXCLUDED.user_id,
            correo = EXCLUDED.correo;

        -- Asegurar registro en adoptantes con user_id
        INSERT INTO public.adoptantes (cedula, user_id)
        VALUES (v_cedula, NEW.id)
        ON CONFLICT (cedula) DO UPDATE
        SET user_id = EXCLUDED.user_id;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_auth_user();

-- ----------------------------------------------------------------------------
-- 8. POLÍTICAS ROW LEVEL SECURITY (RLS) PARA SUPABASE API / FRONTEND
-- ----------------------------------------------------------------------------

ALTER TABLE public.tipomascotas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.localidades ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mascotas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.adoptantes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.solicitudes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.adopciones ENABLE ROW LEVEL SECURITY;

-- Lectura pública para catálogos y mascotas
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'allow_read_tipomascotas') THEN
        CREATE POLICY allow_read_tipomascotas ON public.tipomascotas FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'allow_read_localidades') THEN
        CREATE POLICY allow_read_localidades ON public.localidades FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'allow_read_mascotas') THEN
        CREATE POLICY allow_read_mascotas ON public.mascotas FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'allow_all_solicitudes') THEN
        CREATE POLICY allow_all_solicitudes ON public.solicitudes FOR ALL USING (true) WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'allow_all_usuarios') THEN
        CREATE POLICY allow_all_usuarios ON public.usuarios FOR ALL USING (true) WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'allow_all_adoptantes') THEN
        CREATE POLICY allow_all_adoptantes ON public.adoptantes FOR ALL USING (true) WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'allow_all_adopciones') THEN
        CREATE POLICY allow_all_adopciones ON public.adopciones FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;

-- ----------------------------------------------------------------------------
-- 9. DATOS SEMILLA (SEED DATA)
-- ----------------------------------------------------------------------------

-- Tipos de Mascota
INSERT INTO public.tipomascotas (codtipomascota, nomtipomascota) VALUES
    (1, 'Perro'),
    (2, 'Gato'),
    (3, 'Conejo'),
    (4, 'Ave'),
    (5, 'Hamster'),
    (6, 'Cobaya'),
    (7, 'Tortuga'),
    (8, 'Pez'),
    (9, 'Reptil'),
    (10, 'Huron')
ON CONFLICT (codtipomascota) DO UPDATE SET nomtipomascota = EXCLUDED.nomtipomascota;

-- 20 Localidades de Bogotá
INSERT INTO public.localidades (codlocalidad, nomlocalidad) VALUES
    (1, 'Usaquén'),
    (2, 'Chapinero'),
    (3, 'Santa Fe'),
    (4, 'San Cristóbal'),
    (5, 'Usme'),
    (6, 'Tunjuelito'),
    (7, 'Bosa'),
    (8, 'Kennedy'),
    (9, 'Fontibón'),
    (10, 'Engativá'),
    (11, 'Suba'),
    (12, 'Barrios Unidos'),
    (13, 'Teusaquillo'),
    (14, 'Los Mártires'),
    (15, 'Antonio Nariño'),
    (16, 'Puente Aranda'),
    (17, 'La Candelaria'),
    (18, 'Rafael Uribe Uribe'),
    (19, 'Ciudad Bolívar'),
    (20, 'Sumapaz')
ON CONFLICT (codlocalidad) DO UPDATE SET nomlocalidad = EXCLUDED.nomlocalidad;

-- Usuario y Adoptante de Prueba
INSERT INTO public.usuarios (cedula, correo, nombre, tipouser) VALUES
    ('1001', 'adoptante.demo@example.com', 'Carlos Demo Adoptante', 'adoptante')
ON CONFLICT (cedula) DO UPDATE SET
    correo = EXCLUDED.correo,
    nombre = EXCLUDED.nombre;

INSERT INTO public.adoptantes (cedula, direccion, telefono, codlocalidad) VALUES
    ('1001', 'Calle 100 # 15-20, Bogotá', '3001234567', 1)
ON CONFLICT (cedula) DO UPDATE SET
    direccion = EXCLUDED.direccion,
    telefono = EXCLUDED.telefono,
    codlocalidad = EXCLUDED.codlocalidad;

-- Mascotas en estado disponible para pruebas iniciales
INSERT INTO public.mascotas (codmascota, nombre, especie, estado, codtipomascota) VALUES
    (10, 'Luna', 'Canino', 'disponible', 1),
    (11, 'Toby', 'Canino', 'en_proceso', 1),
    (12, 'Max', 'Canino', 'disponible', 1),
    (15, 'Milo', 'Felino', 'disponible', 2),
    (20, 'Nina', 'Felino', 'disponible', 2),
    (30, 'Bella', 'Lagomorfo', 'disponible', 3)
ON CONFLICT (codmascota) DO UPDATE SET
    nombre = EXCLUDED.nombre,
    especie = EXCLUDED.especie,
    estado = EXCLUDED.estado,
    codtipomascota = EXCLUDED.codtipomascota;

-- Sincronizar secuencia de mascotas con el máximo codmascota
SELECT setval(pg_get_serial_sequence('public.mascotas', 'codmascota'), COALESCE(MAX(codmascota), 1)) FROM public.mascotas;
