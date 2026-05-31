-- ============================================================
-- SwiftPlatform 数据库初始化脚本
-- 数据库：PostgreSQL 15+
-- 字符集：UTF-8
-- 执行方式：psql -U swift -d swift_platform -f scripts/init.sql
-- ============================================================

-- ============================================================
-- 一、系统管理表
-- ============================================================

-- 1. 部门表（树结构）
CREATE TABLE sys_dept (
    id          BIGSERIAL PRIMARY KEY,
    parent_id   BIGINT DEFAULT 0         NOT NULL,
    ancestors   VARCHAR(500) DEFAULT ''  NOT NULL,
    dept_name   VARCHAR(100)             NOT NULL,
    sort_order  INT DEFAULT 0            NOT NULL,
    leader      VARCHAR(50) DEFAULT '',
    phone       VARCHAR(20) DEFAULT '',
    email       VARCHAR(100) DEFAULT '',
    status      SMALLINT DEFAULT 1       NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()  NOT NULL,
    updated_at  TIMESTAMP DEFAULT NOW()  NOT NULL,
    deleted_at  TIMESTAMP
);

COMMENT ON TABLE  sys_dept IS '部门表';
COMMENT ON COLUMN sys_dept.parent_id IS '父部门ID，0表示顶级';
COMMENT ON COLUMN sys_dept.ancestors IS '祖级列表，如 0,1,3';
COMMENT ON COLUMN sys_dept.status    IS '状态：1=正常 0=停用';

-- 5. 岗位表（先创建，用户表有外键）
CREATE TABLE sys_post (
    id          BIGSERIAL PRIMARY KEY,
    post_code   VARCHAR(50) UNIQUE       NOT NULL,
    post_name   VARCHAR(100)             NOT NULL,
    sort_order  INT DEFAULT 0            NOT NULL,
    status      SMALLINT DEFAULT 1       NOT NULL,
    remark      VARCHAR(500) DEFAULT '',
    created_at  TIMESTAMP DEFAULT NOW()  NOT NULL,
    updated_at  TIMESTAMP DEFAULT NOW()  NOT NULL
);

COMMENT ON TABLE sys_post IS '岗位表';

-- 2. 用户表
CREATE TABLE sys_user (
    id          BIGSERIAL PRIMARY KEY,
    username    VARCHAR(50) UNIQUE       NOT NULL,
    password    VARCHAR(200)             NOT NULL,
    nickname    VARCHAR(50) DEFAULT ''   NOT NULL,
    email       VARCHAR(100) DEFAULT '',
    phone       VARCHAR(20) DEFAULT '',
    avatar      VARCHAR(500) DEFAULT '',
    gender      SMALLINT DEFAULT 0       NOT NULL,
    dept_id     BIGINT,
    post_id     BIGINT,
    status      SMALLINT DEFAULT 1       NOT NULL,
    login_ip    VARCHAR(50) DEFAULT '',
    login_at    TIMESTAMP,
    remark      VARCHAR(500) DEFAULT '',
    created_at  TIMESTAMP DEFAULT NOW()  NOT NULL,
    updated_at  TIMESTAMP DEFAULT NOW()  NOT NULL,
    deleted_at  TIMESTAMP,
    CONSTRAINT fk_user_dept FOREIGN KEY (dept_id) REFERENCES sys_dept(id),
    CONSTRAINT fk_user_post FOREIGN KEY (post_id) REFERENCES sys_post(id)
);

COMMENT ON TABLE  sys_user IS '系统用户表';
COMMENT ON COLUMN sys_user.status IS '状态：1=正常 0=停用';

CREATE INDEX idx_user_username ON sys_user(username);
CREATE INDEX idx_user_dept     ON sys_user(dept_id);

-- 3. 角色表
CREATE TABLE sys_role (
    id          BIGSERIAL PRIMARY KEY,
    role_name   VARCHAR(50)              NOT NULL,
    role_key    VARCHAR(50) UNIQUE       NOT NULL,
    sort_order  INT DEFAULT 0            NOT NULL,
    status      SMALLINT DEFAULT 1       NOT NULL,
    remark      VARCHAR(500) DEFAULT '',
    created_at  TIMESTAMP DEFAULT NOW()  NOT NULL,
    updated_at  TIMESTAMP DEFAULT NOW()  NOT NULL
);

COMMENT ON TABLE sys_role IS '角色表';

-- 4. 用户-角色关联表
CREATE TABLE sys_user_role (
    user_id     BIGINT NOT NULL,
    role_id     BIGINT NOT NULL,
    PRIMARY KEY (user_id, role_id),
    CONSTRAINT fk_ur_user FOREIGN KEY (user_id) REFERENCES sys_user(id),
    CONSTRAINT fk_ur_role FOREIGN KEY (role_id) REFERENCES sys_role(id)
);

-- 6. 菜单/权限表
CREATE TABLE sys_menu (
    id          BIGSERIAL PRIMARY KEY,
    parent_id   BIGINT DEFAULT 0         NOT NULL,
    menu_name   VARCHAR(100)             NOT NULL,
    menu_type   CHAR(1) DEFAULT 'M'      NOT NULL,
    sort_order  INT DEFAULT 0            NOT NULL,
    path        VARCHAR(200) DEFAULT '',
    component   VARCHAR(200) DEFAULT '',
    perms       VARCHAR(200) DEFAULT '',
    icon        VARCHAR(100) DEFAULT '#',
    visible     SMALLINT DEFAULT 1       NOT NULL,
    status      SMALLINT DEFAULT 1       NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()  NOT NULL,
    updated_at  TIMESTAMP DEFAULT NOW()  NOT NULL
);

COMMENT ON TABLE  sys_menu IS '菜单权限表';
COMMENT ON COLUMN sys_menu.menu_type IS '类型：M=目录 C=菜单 F=按钮';
COMMENT ON COLUMN sys_menu.perms     IS '权限标识，如 sys:user:add';

-- 7. 角色-菜单关联表
CREATE TABLE sys_role_menu (
    role_id     BIGINT NOT NULL,
    menu_id     BIGINT NOT NULL,
    PRIMARY KEY (role_id, menu_id),
    CONSTRAINT fk_rm_role FOREIGN KEY (role_id) REFERENCES sys_role(id),
    CONSTRAINT fk_rm_menu FOREIGN KEY (menu_id) REFERENCES sys_menu(id)
);

-- 8. 字典类型表
CREATE TABLE sys_dict_type (
    id          BIGSERIAL PRIMARY KEY,
    dict_name   VARCHAR(100)             NOT NULL,
    dict_type   VARCHAR(100) UNIQUE      NOT NULL,
    status      SMALLINT DEFAULT 1       NOT NULL,
    remark      VARCHAR(500) DEFAULT '',
    created_at  TIMESTAMP DEFAULT NOW()  NOT NULL,
    updated_at  TIMESTAMP DEFAULT NOW()  NOT NULL
);

COMMENT ON TABLE sys_dict_type IS '字典类型表';

-- 9. 字典数据表
CREATE TABLE sys_dict_data (
    id          BIGSERIAL PRIMARY KEY,
    dict_type   VARCHAR(100)             NOT NULL,
    dict_label  VARCHAR(100)             NOT NULL,
    dict_value  VARCHAR(100)             NOT NULL,
    sort_order  INT DEFAULT 0            NOT NULL,
    css_class   VARCHAR(100) DEFAULT '',
    status      SMALLINT DEFAULT 1       NOT NULL,
    remark      VARCHAR(500) DEFAULT '',
    created_at  TIMESTAMP DEFAULT NOW()  NOT NULL
);

COMMENT ON TABLE sys_dict_data IS '字典数据表';
CREATE INDEX idx_dict_type ON sys_dict_data(dict_type);

-- 10. 操作日志表
CREATE TABLE sys_log (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT,
    username    VARCHAR(50) DEFAULT '',
    module      VARCHAR(50) DEFAULT '',
    action      VARCHAR(100) DEFAULT '',
    method      VARCHAR(10) DEFAULT '',
    url         VARCHAR(500) DEFAULT '',
    ip          VARCHAR(50) DEFAULT '',
    user_agent  VARCHAR(500) DEFAULT '',
    params      TEXT DEFAULT '',
    result      TEXT DEFAULT '',
    status_code INT DEFAULT 200,
    error_msg   TEXT DEFAULT '',
    duration    INT DEFAULT 0,
    created_at  TIMESTAMP DEFAULT NOW()  NOT NULL
);

COMMENT ON TABLE sys_log IS '操作日志表';
CREATE INDEX idx_log_user ON sys_log(user_id);
CREATE INDEX idx_log_time ON sys_log(created_at);

-- 11. 系统配置表
CREATE TABLE sys_config (
    id           BIGSERIAL PRIMARY KEY,
    config_name  VARCHAR(100)            NOT NULL,
    config_key   VARCHAR(100) UNIQUE     NOT NULL,
    config_value TEXT DEFAULT ''          NOT NULL,
    remark       VARCHAR(500) DEFAULT '',
    created_at   TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at   TIMESTAMP DEFAULT NOW() NOT NULL
);

COMMENT ON TABLE sys_config IS '系统配置表';

-- ============================================================
-- 二、流程引擎表
-- ============================================================

-- 12. 流程定义表
CREATE TABLE wf_definition (
    id              BIGSERIAL PRIMARY KEY,
    name            VARCHAR(200)            NOT NULL,
    code            VARCHAR(100) UNIQUE     NOT NULL,
    description     TEXT DEFAULT '',
    category        VARCHAR(100) DEFAULT '',
    form_config     JSONB DEFAULT '{}',
    graph_data      JSONB DEFAULT '{}',
    node_config     JSONB DEFAULT '{}',
    version         INT DEFAULT 1           NOT NULL,
    status          SMALLINT DEFAULT 0      NOT NULL,
    created_by      BIGINT,
    created_at      TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at      TIMESTAMP DEFAULT NOW() NOT NULL
);

COMMENT ON TABLE  wf_definition IS '流程定义表';
COMMENT ON COLUMN wf_definition.form_config IS '表单字段配置，JSON Schema 格式';
COMMENT ON COLUMN wf_definition.graph_data  IS '流程图结构数据，LogicFlow JSON 格式';
COMMENT ON COLUMN wf_definition.status      IS '0=草稿 1=已发布 2=已停用';

-- 13. 流程实例表
CREATE TABLE wf_instance (
    id              BIGSERIAL PRIMARY KEY,
    definition_id   BIGINT                  NOT NULL,
    title           VARCHAR(500)            NOT NULL,
    business_key    VARCHAR(200) DEFAULT '',
    form_data       JSONB DEFAULT '{}',
    initiator_id    BIGINT                  NOT NULL,
    current_node    VARCHAR(100) DEFAULT '',
    status          SMALLINT DEFAULT 0      NOT NULL,
    started_at      TIMESTAMP DEFAULT NOW() NOT NULL,
    finished_at     TIMESTAMP,
    CONSTRAINT fk_inst_def  FOREIGN KEY (definition_id) REFERENCES wf_definition(id),
    CONSTRAINT fk_inst_user FOREIGN KEY (initiator_id)  REFERENCES sys_user(id)
);

COMMENT ON TABLE  wf_instance IS '流程实例表';
COMMENT ON COLUMN wf_instance.business_key IS '关联业务数据，格式：表名:ID';
COMMENT ON COLUMN wf_instance.status       IS '0=进行中 1=已通过 2=已驳回 3=已撤回 4=已终止';

CREATE INDEX idx_inst_def    ON wf_instance(definition_id);
CREATE INDEX idx_inst_user   ON wf_instance(initiator_id);
CREATE INDEX idx_inst_status ON wf_instance(status);

-- 14. 待办任务表
CREATE TABLE wf_task (
    id              BIGSERIAL PRIMARY KEY,
    instance_id     BIGINT                  NOT NULL,
    node_id         VARCHAR(100)            NOT NULL,
    node_name       VARCHAR(200) DEFAULT '',
    node_type       VARCHAR(50) DEFAULT 'approval',
    assignee_id     BIGINT,
    assignee_type   VARCHAR(50) DEFAULT 'user',
    action          VARCHAR(50) DEFAULT '',
    comment         TEXT DEFAULT '',
    status          SMALLINT DEFAULT 0      NOT NULL,
    due_at          TIMESTAMP,
    processed_at    TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW() NOT NULL,
    CONSTRAINT fk_task_inst  FOREIGN KEY (instance_id) REFERENCES wf_instance(id),
    CONSTRAINT fk_task_user  FOREIGN KEY (assignee_id) REFERENCES sys_user(id)
);

COMMENT ON TABLE  wf_task IS '流程待办任务表';
COMMENT ON COLUMN wf_task.status IS '0=待处理 1=已通过 2=已驳回 3=已转办 4=已撤回';

CREATE INDEX idx_task_instance ON wf_task(instance_id);
CREATE INDEX idx_task_assignee ON wf_task(assignee_id);
CREATE INDEX idx_task_status   ON wf_task(status);

-- 15. 流程历史记录表
CREATE TABLE wf_history (
    id              BIGSERIAL PRIMARY KEY,
    instance_id     BIGINT                  NOT NULL,
    node_id         VARCHAR(100)            NOT NULL,
    node_name       VARCHAR(200) DEFAULT '',
    operator_id     BIGINT,
    action          VARCHAR(50)             NOT NULL,
    comment         TEXT DEFAULT '',
    form_snapshot   JSONB DEFAULT '{}',
    created_at      TIMESTAMP DEFAULT NOW() NOT NULL,
    CONSTRAINT fk_hist_inst FOREIGN KEY (instance_id) REFERENCES wf_instance(id)
);

COMMENT ON TABLE wf_history IS '流程流转历史表';
CREATE INDEX idx_hist_instance ON wf_history(instance_id);

-- ============================================================
-- 三、初始化数据
-- ============================================================

-- 初始化岗位（先于用户，因为用户有外键约束）
INSERT INTO sys_post (post_code, post_name, sort_order) VALUES
('ceo', '总经理', 1),
('dev', '开发工程师', 2),
('pm',  '产品经理', 3),
('hr',  '人事专员', 4);

-- 初始化部门
INSERT INTO sys_dept (parent_id, ancestors, dept_name, sort_order) VALUES
(0, '0',     '总公司',   0),
(1, '0,1',   '技术部',   1),
(1, '0,1',   '市场部',   2),
(1, '0,1',   '财务部',   3);

-- 初始化超级管理员（密码: admin123，bcrypt 加密）
-- 生成方式：python -c "import bcrypt; print(bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode())"
INSERT INTO sys_user (username, password, nickname, gender, dept_id, post_id, status) VALUES
('admin', '$2b$12$O2LwSGmpBK2d3gV.Ka3e6Oxz1AWz4FFjQm8qJ5s2bEzf4ct4F3MZW', '超级管理员', 1, 1, 1, 1);

-- 初始化角色
INSERT INTO sys_role (role_name, role_key, sort_order) VALUES
('超级管理员', 'super_admin', 1),
('普通用户',   'user',        2);

-- 管理员绑定角色
INSERT INTO sys_user_role (user_id, role_id) VALUES (1, 1);

-- 初始化菜单
INSERT INTO sys_menu (id, parent_id, menu_name, menu_type, sort_order, path, component, perms, icon) VALUES
-- 一级目录
(1,  0, '系统管理', 'M', 1, '/system',    '',                               '',                   'SettingOutlined'),
(2,  0, '流程管理', 'M', 2, '/workflow',   '',                               '',                   'BranchesOutlined'),
-- 系统管理 - 二级菜单
(10, 1, '用户管理', 'C', 1, 'user',       'system/user/index',              'sys:user:list',      'UserOutlined'),
(11, 1, '角色管理', 'C', 2, 'role',       'system/role/index',              'sys:role:list',      'TeamOutlined'),
(12, 1, '部门管理', 'C', 3, 'dept',       'system/dept/index',              'sys:dept:list',      'ApartmentOutlined'),
(13, 1, '岗位管理', 'C', 4, 'post',       'system/post/index',              'sys:post:list',      'SolutionOutlined'),
(14, 1, '菜单管理', 'C', 5, 'menu',       'system/menu/index',              'sys:menu:list',      'MenuOutlined'),
(15, 1, '字典管理', 'C', 6, 'dict',       'system/dict/index',              'sys:dict:list',      'BookOutlined'),
(16, 1, '操作日志', 'C', 7, 'log',        'system/log/index',               'sys:log:list',       'FileTextOutlined'),
(17, 1, '系统配置', 'C', 8, 'config',     'system/config/index',            'sys:config:list',    'ToolOutlined'),
-- 用户管理 - 按钮权限
(101, 10, '用户新增', 'F', 1, '', '', 'sys:user:add',    '#'),
(102, 10, '用户编辑', 'F', 2, '', '', 'sys:user:edit',   '#'),
(103, 10, '用户删除', 'F', 3, '', '', 'sys:user:delete',  '#'),
(104, 10, '重置密码', 'F', 4, '', '', 'sys:user:reset',  '#'),
(105, 10, '用户导出', 'F', 5, '', '', 'sys:user:export', '#'),
-- 角色管理 - 按钮权限
(111, 11, '角色新增', 'F', 1, '', '', 'sys:role:add',    '#'),
(112, 11, '角色编辑', 'F', 2, '', '', 'sys:role:edit',   '#'),
(113, 11, '角色删除', 'F', 3, '', '', 'sys:role:delete',  '#'),
(114, 11, '分配权限', 'F', 4, '', '', 'sys:role:perm',   '#'),
-- 部门管理 - 按钮权限
(121, 12, '部门新增', 'F', 1, '', '', 'sys:dept:add',    '#'),
(122, 12, '部门编辑', 'F', 2, '', '', 'sys:dept:edit',   '#'),
(123, 12, '部门删除', 'F', 3, '', '', 'sys:dept:delete',  '#'),
-- 岗位管理 - 按钮权限
(131, 13, '岗位新增', 'F', 1, '', '', 'sys:post:add',    '#'),
(132, 13, '岗位编辑', 'F', 2, '', '', 'sys:post:edit',   '#'),
(133, 13, '岗位删除', 'F', 3, '', '', 'sys:post:delete',  '#'),
-- 菜单管理 - 按钮权限
(141, 14, '菜单新增', 'F', 1, '', '', 'sys:menu:add',    '#'),
(142, 14, '菜单编辑', 'F', 2, '', '', 'sys:menu:edit',   '#'),
(143, 14, '菜单删除', 'F', 3, '', '', 'sys:menu:delete',  '#'),
(144, 14, '菜单排序', 'F', 4, '', '', 'sys:menu:sort',   '#'),
-- 字典管理 - 按钮权限
(151, 15, '字典新增', 'F', 1, '', '', 'sys:dict:add',    '#'),
(152, 15, '字典编辑', 'F', 2, '', '', 'sys:dict:edit',   '#'),
(153, 15, '字典删除', 'F', 3, '', '', 'sys:dict:delete',  '#'),
-- 流程管理 - 二级菜单
(20, 2, '流程定义', 'C', 1, 'definition', 'workflow/definition/index',     'wf:def:list',        'NodeIndexOutlined'),
(21, 2, '流程实例', 'C', 2, 'instance',   'workflow/instance/index',       'wf:inst:list',       'DeploymentUnitOutlined'),
(22, 2, '我的待办', 'C', 3, 'todo',       'workflow/todo/index',           'wf:todo:list',       'ClockCircleOutlined'),
(23, 2, '我的已办', 'C', 4, 'done',       'workflow/done/index',           'wf:done:list',       'CheckCircleOutlined'),
-- 流程定义 - 按钮权限
(201, 20, '新建流程', 'F', 1, '', '', 'wf:def:add',     '#'),
(202, 20, '编辑流程', 'F', 2, '', '', 'wf:def:edit',    '#'),
(203, 20, '发布流程', 'F', 3, '', '', 'wf:def:publish', '#'),
(204, 20, '停用流程', 'F', 4, '', '', 'wf:def:disable', '#'),
(205, 20, '删除流程', 'F', 5, '', '', 'wf:def:delete',  '#');

-- 超级管理员拥有所有菜单权限
INSERT INTO sys_role_menu (role_id, menu_id)
SELECT 1, id FROM sys_menu;

-- 初始化字典类型
INSERT INTO sys_dict_type (dict_name, dict_type) VALUES
('用户性别',   'sys_user_gender'),
('系统状态',   'sys_status'),
('流程状态',   'wf_instance_status'),
('任务状态',   'wf_task_status'),
('流程分类',   'wf_category');

-- 初始化字典数据
INSERT INTO sys_dict_data (dict_type, dict_label, dict_value, sort_order) VALUES
('sys_user_gender', '未知', '0', 1),
('sys_user_gender', '男',   '1', 2),
('sys_user_gender', '女',   '2', 3),
('sys_status', '正常', '1', 1),
('sys_status', '停用', '0', 2),
('wf_instance_status', '进行中', '0', 1),
('wf_instance_status', '已通过', '1', 2),
('wf_instance_status', '已驳回', '2', 3),
('wf_instance_status', '已撤回', '3', 4),
('wf_instance_status', '已终止', '4', 5),
('wf_task_status', '待处理', '0', 1),
('wf_task_status', '已通过', '1', 2),
('wf_task_status', '已驳回', '2', 3),
('wf_task_status', '已转办', '3', 4),
('wf_category', 'OA办公',   'oa',      1),
('wf_category', '设备管理',  'device',  2),
('wf_category', '财务管理',  'finance', 3),
('wf_category', '项目管理',  'project', 4),
('wf_category', '其他',      'other',   5);

-- 初始化系统配置
INSERT INTO sys_config (config_name, config_key, config_value) VALUES
('网站名称',    'sys.app.name',         'SwiftPlatform'),
('登录验证码',  'sys.login.captcha',    'false'),
('用户初始密码', 'sys.user.init_pwd',   '123456'),
('文件上传大小(MB)', 'sys.upload.max_size', '10');

-- 完成
SELECT '✅ 数据库初始化完成' AS result;
