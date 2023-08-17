
--
-- Name: projects; Type: TABLE; Schema: public; Owner: petrellocator; Tablespace:
--

CREATE TABLE projects (
    id integer NOT NULL,
    project_filename character varying(4096) NOT NULL,
    project_size bigint,
    project_name character varying(255),
    project_lastmodified timestamp without time zone,
    process_flag smallint,
    last_crawl_date timestamp without time zone,
    processing_time integer,
    process_exit_code integer,
    process_error_count integer,
    last_process_date timestamp without time zone
);


ALTER TABLE public.projects OWNER TO petrellocator;

--
-- Name: projects_id_seq; Type: SEQUENCE; Schema: public; Owner: petrellocator
--

CREATE SEQUENCE projects_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.projects_id_seq OWNER TO petrellocator;

--
-- Name: projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: petrellocator
--

ALTER SEQUENCE projects_id_seq OWNED BY projects.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: petrellocator
--

ALTER TABLE ONLY projects ALTER COLUMN id SET DEFAULT nextval('projects_id_seq'::regclass);


--
-- Name: projects_project_filename_key; Type: CONSTRAINT; Schema: public; Owner: petrellocator; Tablespace:
--

ALTER TABLE ONLY projects
    ADD CONSTRAINT projects_project_filename_key UNIQUE (project_filename);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

