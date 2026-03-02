#ifndef WIDGET_H
#define WIDGET_H

#include <QWidget>
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>
#include <QTextEdit>
#include <QProcess>

QT_BEGIN_NAMESPACE
namespace Ui {
class Widget;
}
QT_END_NAMESPACE

class Widget : public QWidget
{
    Q_OBJECT

public:
    Widget(QWidget* parent = nullptr);
    ~Widget();

private slots:

    void onSubmitClicked();             // 提交/开始下载按钮的按下逻辑

private:
    Ui::Widget* ui;

    void setUi();                       // 设置/创建页面的结构
    void setUiBusy(bool busy);          // busy=true时禁用输入和按钮，防止重复提交。busy=false时恢复控件可用状态。
    QString py_venv_path() const;       // 解析python解释器路径
    QString py_scr_path() const;        // 解析python脚本代码路径
    void append_logText(const QString log_text);    // 追加日志信息

    QProcess* pyProcess;
    QLineEdit* urlLineEdit;
    QPushButton* submit_button;
    QLabel* state_label;
    QTextEdit* log_textEdit;
};
#endif // WIDGET_H
