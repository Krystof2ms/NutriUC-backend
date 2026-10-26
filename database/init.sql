CREATE DATABASE nutri_uc;

\c nutri_uc

CREATE TABLE "Category" (
    "id" integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "name" text NOT NULL,
    "description" text NOT NULL,
    "type" text NOT NULL,

    CONSTRAINT "Category_name_unique" UNIQUE ("name")
);

CREATE TABLE "Role" (
    "id" integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "name" text NOT NULL,
    "created_at" timestamptz NOT NULL DEFAULT now(),
    "updated_at" timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT "Role_name_unique" UNIQUE ("name")
);

CREATE TABLE "User" (
    "id" bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "public_id" uuid NOT NULL DEFAULT uuidv7(),
    "avatar_key" text,
    "name" text NOT NULL,
    "email" text NOT NULL,
    "password_hash" text,
    "status" text NOT NULL DEFAULT 'active',
    "role_id" integer NOT NULL,

    "created_at" timestamptz NOT NULL DEFAULT now(),
    "updated_at" timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT "User_public_id_unique" UNIQUE ("public_id"),
    CONSTRAINT "User_email_unique" UNIQUE ("email"),

    CONSTRAINT "User_role_id_Role_id_fk"
        FOREIGN KEY ("role_id")
        REFERENCES "Role" ("id")
);

CREATE TABLE "Recipe" (
    "id" bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    "name" text NOT NULL,
    "origin" text NOT NULL,
    "instructions" jsonb NOT NULL,
    "ingredients" jsonb NOT NULL,
    "description" text NOT NULL,

    "category_id" integer NOT NULL,
    "user_id" bigint NOT NULL,

    "image_key" text,

    "created_at" timestamptz NOT NULL DEFAULT now(),
    "updated_at" timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT "Recipe_category_id_Category_id_fk"
        FOREIGN KEY ("category_id")
        REFERENCES "Category" ("id"),

    CONSTRAINT "Recipe_user_id_User_id_fk"
        FOREIGN KEY ("user_id")
        REFERENCES "User" ("id")
);

CREATE TABLE "Session" (
    "id" bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    "jti" uuid NOT NULL,
    "token_hash" text NOT NULL,

    "user_id" bigint NOT NULL,

    "expires_at" timestamptz NOT NULL,
    "revoked" boolean NOT NULL DEFAULT false,
    "created_at" timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT "Session_jti_unique" UNIQUE ("jti"),
    CONSTRAINT "Session_token_hash_unique" UNIQUE ("token_hash"),

    CONSTRAINT "Session_user_id_User_id_fk"
        FOREIGN KEY ("user_id")
        REFERENCES "User" ("id")
);

CREATE TABLE "Tip" (
    "id" bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    "title" text NOT NULL,
    "content" text NOT NULL,

    "category_id" integer NOT NULL,
    "user_id" bigint NOT NULL,

    "created_at" timestamptz NOT NULL DEFAULT now(),
    "updated_at" timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT "Tip_category_id_Category_id_fk"
        FOREIGN KEY ("category_id")
        REFERENCES "Category" ("id"),

    CONSTRAINT "Tip_user_id_User_id_fk"
        FOREIGN KEY ("user_id")
        REFERENCES "User" ("id")
);
