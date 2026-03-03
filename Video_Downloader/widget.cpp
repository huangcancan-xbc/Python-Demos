#include "widget.h"
#include "./ui_widget.h"

#include <QCoreApplication>
#include <QDateTime>
#include <QDir>
#include <QFileInfo>
#include <QMessageBox>
#include <QTextCursor>
#include <QVBoxLayout>

Widget::Widget(QWidget* parent)
    : QWidget(parent)
    , ui(new Ui::Widget)
    , pyProcess(new QProcess(this))
    , urlLineEdit(nullptr)
    , submit_button(nullptr)
    , state_label(nullptr)
    , log_textEdit(nullptr)
{
    ui->setupUi(this);

    setUi();    // 创建页面

    // 子进程通道模式：SeparateChannels = stdout/stderr分离，便于在ui中单独标识错误输出
    pyProcess->setProcessChannelMode(QProcess::SeparateChannels);


    // 按钮点击 -> 提交下载流程入口。
    connect(submit_button, &QPushButton::clicked, this, &Widget::onSubmitClicked);

    // 子进程标准输出：读取并追加到日志框
    connect(pyProcess, &QProcess::readyReadStandardOutput, this, &Widget::handleProcessStdout);

    // 子进程标准错误：读取并追加到日志框（含错误前缀）
    connect(pyProcess, &QProcess::readyReadStandardError, this, &Widget::handleProcessStderr);

    // 子进程Process级别的错误处理：自身错误（比如启动失败）回调
    connect(pyProcess, &QProcess::errorOccurred, this, &Widget::handleProcessError);

    // 子进程结束统一处理方式
    connect(pyProcess, &QProcess::finished, this, &Widget::handleProcessFinished);

    append_logText("[info] 应用已经启动！准备好开始下载您的视频了吗……");
    append_logText(QString("[info] 当前视频输出目录：%1").arg(QDir::toNativeSeparators(QDir::currentPath())));
}

Widget::~Widget()
{
    if (pyProcess->state() != QProcess::NotRunning)
    {
        // terminate() 会请求子进程正常结束；
        // waitForFinished(1500) 最多等 1.5 秒，避免界面退出时长时间阻塞。
        pyProcess->terminate();
        pyProcess->waitForFinished(1500);
    }

    delete ui;
}

void Widget::setUi()
{
    setWindowTitle("Qt + Python 视频下载器");    // 设置窗口标题

    auto* layout = new QVBoxLayout(this);       // 创建垂直布局管理器
    layout->setContentsMargins(12, 12, 12, 12); // 设置内边距，参数顺序：左、上、右、下
    layout->setSpacing(12);                     // 设置同一布局中，各个控件/子布局之间的间距

    QLabel* tip_title = new QLabel("粘贴视频链接后点击“开始下载”，程序会调用 Python 脚本进行下载。", this);   // 提示文字标题
    tip_title->setWordWrap(true);               // 设置自动换行

    urlLineEdit = new QLineEdit(this);          // 输入视频链接的输入框
    urlLineEdit->setPlaceholderText("https://www.youtube.com/watch?v=...");  // 输入框中的提示性文字（占位提示文本）
    urlLineEdit->setClearButtonEnabled(true);   // 显示清空按钮（×），可以一键清空内容

    submit_button = new QPushButton("开始下载", this);                  // 提交按钮
    state_label = new QLabel("状态：空闲/可用", this);                   // 状态信息（每次只能下载一个）

    log_textEdit = new QTextEdit(this);
    log_textEdit->setReadOnly(true);            // 只读
    log_textEdit->setPlaceholderText("Python 后端日志会显示在这里。");   // 提示性文字（占位提示文本）

    // 设置布局和垂直方向的拉伸系数生效
    urlLineEdit->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
    submit_button->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
    layout->addWidget(tip_title, 1);
    layout->addWidget(urlLineEdit, 1);
    layout->addWidget(submit_button, 1);
    layout->addWidget(state_label, 1);
    layout->addWidget(log_textEdit, 6);
}

void Widget::setUiBusy(bool busy)
{
    // 任务运行中禁用输入，避免“连续点击”触发重复任务。
    state_label->setEnabled(!busy);
    state_label->setEnabled(!busy);

    if(busy)
    {
        state_label->setText("状态：运行中");
    }
    else if(state_label->text() == "状态：运行中")
    {
        // 只有仍处于“运行中”时才回落到“空闲”，避免覆盖“成功/失败”。
        state_label->setText("状态：空闲/可用");
    }
}

void Widget::onSubmitClicked()
{
    // 一次只允许一个下载任务，避免并发覆盖日志和状态
    // state()用于获取进程实时状态，QProcess::NotRunning是进程未运行的标识
    // QProcess::NotRunning (0)：进程未运行（初始状态或已结束/崩溃）
    // QProcess::Starting (1)：正在启动中（程序还未真正运行）
    // QProcess::Running (2)：进程正在运行，可读写
    if (pyProcess->state() != QProcess::NotRunning)
    {
        QMessageBox::information(this, "任务进行中", "已有下载任务正在运行。");
        return;
    }

    // trimmed()去除首尾空白，避免用户输入异常
    const QString videoUrl = urlLineEdit->text().trimmed();
    if (videoUrl.isEmpty())
    {
        QMessageBox::warning(this, "缺少链接", "请先输入视频链接！");
        return;
    }

    const QString pyVenvPath = py_venv_path();      // 解释器路径
    const QString pySrcPath = py_scr_path();        // python脚本代码路径
    if (pyVenvPath.isEmpty())
    {
        QMessageBox::critical(this, "未找到 Python 虚拟环境", "未找到 .venv 中的 Python 解释器。\n");
        append_logText("错误：未在项目目录或上级目录找到 Python 解释器（.venv）。");
        return;
    }
    if (pySrcPath.isEmpty())
    {
        QMessageBox::critical(this, "未找到后端脚本", "未找到 python/download_video.py。");
        append_logText("错误：未找到后端脚本 python/download_video.py。");
        return;
    }

    // 当前输出路径
    const QString outputPath = QDir::currentPath();
    // 用于python编译的参数选项信息，相当于gcc -o 中的 -o
    QStringList Compilation_options;
    Compilation_options << "-u" << pySrcPath << "--url" << videoUrl << "--output-dir" << outputPath;

    // QDir::toNativeSeparators()用于把路径中的斜杠转为当前系统原生分隔符
    // Windows 输出：C:\Videos\Downloads
    // Linux/macOS 输出：C:/Videos/Downloads
    append_logText("------------------------------------------------------------------------------------------------------");
    append_logText(QString("[debug] 开始时间：%1").arg(QDateTime::currentDateTime().toString(Qt::ISODate)));
    append_logText(QString("[debug] Python 解释器：%1").arg(QDir::toNativeSeparators(pyVenvPath)));
    append_logText(QString("[debug] Python 后端脚本：%1").arg(QDir::toNativeSeparators(pySrcPath)));
    append_logText(QString("[debug] 下载的视频链接：%1").arg(videoUrl));
    append_logText(QString("[debug] 视频输出目录：%1").arg(QDir::toNativeSeparators(outputPath)));
    append_logText("------------------------------------------------------------------------------------------------------");

    // 标记繁忙——运行中
    setUiBusy(true);

    // 设置子进程的工作目录
    pyProcess->setWorkingDirectory(outputPath);
    // 启动外部进程，等价于命令行执行：pythonExe -u scriptPath --url xxx --output-dir xxx 作用：
    // 第一个参数：QString program：要执行的程序路径（如 "python.exe" 或 "/usr/bin/python3"）
    // 第二个参数：QStringList Compilation_options：传给程序的命令行参数列表（这里包含 -u、脚本路径、--url 等）
    // 异步启动 Python 脚本
    // 通过进程边界调用（不需在 C++ 链接 Python）
    // 完成后可通过 readyReadStandardOutput / finished 信号获取结果
    pyProcess->start(pyVenvPath, Compilation_options);
}

// 处理子进程的标准输出
void Widget::handleProcessStdout()
{
    // fromLocal8Bit：按本地编码解码字节流，减少中文日志乱码概率
    append_logText(QString::fromLocal8Bit(pyProcess->readAllStandardOutput()));
}

// 处理子进程的标准错误
void Widget::handleProcessStderr()
{
    // stderr通常是错误/警告信息，这里统一加前缀便于肉眼筛查。
    const QString stderrText = QString::fromLocal8Bit(pyProcess->readAllStandardError());
    append_logText(QString("[标准错误] %1").arg(stderrText));
}

// 处理QProcess级别的错误
void Widget::handleProcessError(QProcess::ProcessError error)
{
    // 把QProcess枚举转成可读文本，便于排查
    QString errorName;
    switch (error)
    {
        case QProcess::FailedToStart:
            errorName = "启动失败";
            break;
        case QProcess::Crashed:
            errorName = "进程崩溃";
            break;
        case QProcess::Timedout:
            errorName = "超时";
            break;
        case QProcess::ReadError:
            errorName = "读取错误";
            break;
        case QProcess::WriteError:
            errorName = "写入错误";
            break;
        case QProcess::UnknownError:
        default:
            errorName = "未知错误";
            break;
    }

    append_logText(QString("错误：QProcess 级别的错误! QProcess 错误类型：%1").arg(errorName));
    append_logText(QString("错误详情：%1").arg(pyProcess->errorString()));

    setUiBusy(false);
    state_label->setText("状态：失败！");
}

// 统一处理进程结束后的逻辑
void Widget::handleProcessFinished(int exitCode, QProcess::ExitStatus exitStatus)
{
    setUiBusy(false);       // 无论成功失败，任务都结束了，先恢复可交互状态

    if (exitStatus == QProcess::CrashExit)
    {
        append_logText("错误：Python 子进程异常崩溃。");
        state_label->setText("状态：失败！");
        QMessageBox::critical(this, "下载失败", "Python 子进程异常崩溃！");
        return;
    }

    if (exitCode == 0)
    {
        append_logText("成功：下载任务已完成！");
        state_label->setText("状态：成功！");
        QMessageBox::information(this, "完成", "视频下载完成！");
        return;
    }

    append_logText(QString("错误：Python 子进程退出码为 %1").arg(exitCode));
    state_label->setText("状态：失败！");
    QMessageBox::warning(this, "下载失败", QString("Python 脚本以退出码 %1 结束。\n请查看日志定位问题。").arg(exitCode));
}

QString Widget::py_venv_path() const
{
    const QString curPath = QString::fromUtf8("."); // 当前路径
    // 优先使用项目虚拟环境
    const QStringList paths = {
       QDir(curPath).filePath("../../.venv/Scripts/python.exe"),
       QDir(curPath).filePath("../../.venv/bin/python"),
       QDir::current().filePath("../../.venv/Scripts/python.exe"),
       QDir::current().filePath("../../.venv/bin/python")
    };

    for (const QString& path : paths)
    {
        // QFileInfo 用于跨平台判断“是否存在且是普通文件”。
        // info.exists()          文件/目录是否存在
        // info.isFile()          是普通文件
        // info.isDir()           是目录
        // info.isExecutable()    是否可执行
        // info.absoluteFilePath()  返回规范化的绝对路径
        // info.fileName()        只取文件名
        // info.size()            文件大小（字节）
        QFileInfo info(path);
        if (info.exists() && info.isFile())
        {
            return info.absoluteFilePath();
        }
    }

    return QString();
}

QString Widget::py_scr_path() const
{
    const QString curPath = QString::fromUtf8(".");
    // 先找源码目录，再找当前目录和可执行目录，兼容不同启动方式。
    const QStringList paths = {
        QDir(curPath).filePath("../../python/download_video.py"),
        QDir::current().filePath("../../python/download_video.py"),
        QDir(QCoreApplication::applicationDirPath()).filePath("../../python/download_video.py")
    };

    for (const QString& path : paths)
    {
        QFileInfo info(path);
        if (info.exists() && info.isFile())
        {
            return info.absoluteFilePath();
        }
    }

    return QString();
}

void Widget::append_logText(const QString log_text)
{
    if (log_text.isEmpty())
    {
        return;
    }

    // 先把光标移到末尾，再插入文本，保证日志按时间顺序追加。
    log_textEdit->moveCursor(QTextCursor::End);
    log_textEdit->insertPlainText(log_text);

    // 每次写入都补齐换行，避免多条日志粘连在一行。
    if (!log_text.endsWith('\n'))
    {
        log_textEdit->insertPlainText("\n");
    }

    // 再次移动到底部，确保总能看到最新日志。
    log_textEdit->moveCursor(QTextCursor::End);
}
