--
-- PostgreSQL database dump
--

-- Dumped from database version 14.8 (Debian 14.8-1.pgdg120+1)
-- Dumped by pg_dump version 14.8 (Debian 14.8-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: be_holidays; Type: TABLE; Schema: public; Owner: dbuser
--

CREATE TABLE public.be_holidays (
    id character varying,
    event_date date,
    holiday_description character varying
);


ALTER TABLE public.be_holidays OWNER TO dbuser;

--
-- Name: source_data_EUR; Type: TABLE; Schema: public; Owner: dbuser
--

CREATE TABLE public."source_data_EUR" (
    id integer NOT NULL,
    upload_dt timestamp without time zone NOT NULL,
    currency character varying(3) NOT NULL,
    rate numeric(10,4)
);


ALTER TABLE public."source_data_EUR" OWNER TO dbuser;

--
-- Name: source_data_USD; Type: TABLE; Schema: public; Owner: dbuser
--

CREATE TABLE public."source_data_USD" (
    id integer NOT NULL,
    upload_dt timestamp without time zone NOT NULL,
    api_data json NOT NULL
);


ALTER TABLE public."source_data_USD" OWNER TO dbuser;

--
-- Name: exchange_rates; Type: VIEW; Schema: public; Owner: dbuser
--

CREATE VIEW public.exchange_rates AS
 SELECT COALESCE(sd_eur.upload_dt, sd_usd.upload_dt) AS upload_dt,
        CASE
            WHEN (sd_eur.id IS NOT NULL) THEN 'EUR'::text
            ELSE 'USD'::text
        END AS base,
    COALESCE(sd_eur.currency, (usd_rates.currency)::character varying) AS currency,
    COALESCE(sd_eur.rate, (usd_rates.rate)::numeric) AS rate,
        CASE
            WHEN (bh.event_date IS NULL) THEN 'No'::text
            ELSE 'Yes'::text
        END AS is_holiday
   FROM (((public."source_data_EUR" sd_eur
     FULL JOIN public."source_data_USD" sd_usd ON ((sd_eur.upload_dt = sd_usd.upload_dt)))
     LEFT JOIN public.be_holidays bh ON (((COALESCE(sd_eur.upload_dt, sd_usd.upload_dt))::date = bh.event_date)))
     LEFT JOIN ( SELECT "source_data_USD".upload_dt,
            (json_each_text(("source_data_USD".api_data -> 'rates'::text))).key AS currency,
            (json_each_text(("source_data_USD".api_data -> 'rates'::text))).value AS rate
           FROM public."source_data_USD") usd_rates ON ((sd_usd.upload_dt = usd_rates.upload_dt)));


ALTER TABLE public.exchange_rates OWNER TO dbuser;

--
-- Name: source_data_EUR_id_seq; Type: SEQUENCE; Schema: public; Owner: dbuser
--

CREATE SEQUENCE public."source_data_EUR_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public."source_data_EUR_id_seq" OWNER TO dbuser;

--
-- Name: source_data_EUR_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dbuser
--

ALTER SEQUENCE public."source_data_EUR_id_seq" OWNED BY public."source_data_EUR".id;


--
-- Name: source_data_USD_id_seq; Type: SEQUENCE; Schema: public; Owner: dbuser
--

CREATE SEQUENCE public."source_data_USD_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public."source_data_USD_id_seq" OWNER TO dbuser;

--
-- Name: source_data_USD_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dbuser
--

ALTER SEQUENCE public."source_data_USD_id_seq" OWNED BY public."source_data_USD".id;


--
-- Name: source_data_EUR id; Type: DEFAULT; Schema: public; Owner: dbuser
--

ALTER TABLE ONLY public."source_data_EUR" ALTER COLUMN id SET DEFAULT nextval('public."source_data_EUR_id_seq"'::regclass);


--
-- Name: source_data_USD id; Type: DEFAULT; Schema: public; Owner: dbuser
--

ALTER TABLE ONLY public."source_data_USD" ALTER COLUMN id SET DEFAULT nextval('public."source_data_USD_id_seq"'::regclass);


--
-- Name: source_data_EUR source_data_EUR_pkey; Type: CONSTRAINT; Schema: public; Owner: dbuser
--

ALTER TABLE ONLY public."source_data_EUR"
    ADD CONSTRAINT "source_data_EUR_pkey" PRIMARY KEY (id);


--
-- Name: source_data_USD source_data_USD_pkey; Type: CONSTRAINT; Schema: public; Owner: dbuser
--

ALTER TABLE ONLY public."source_data_USD"
    ADD CONSTRAINT "source_data_USD_pkey" PRIMARY KEY (id);


--
-- PostgreSQL database dump complete
--
