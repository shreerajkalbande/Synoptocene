import os
import shutil
import subprocess
import time
from functools import wraps
from datetime import date

from flask import (
    Blueprint,
    abort,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify,
    current_app,
)
from flask_login import current_user, login_user, logout_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from web.models import db, User, BlogPost, Comment
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm


ALLOWED_EXTENSIONS = {"mp4", "avi", "mov"}

main_bp = Blueprint("main", __name__)

# State for Selenium sessions (kept as module-level for now)
_global_driver = None
_upload_counter = 0
_final_summary = None


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


# --- Auth routes ---

@main_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        result = db.session.execute(
            db.select(User).where(User.email == form.email.data)
        )
        user = result.scalar()
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for("main.login"))

        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=generate_password_hash(
                form.password.data, method="pbkdf2:sha256", salt_length=8
            ),
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("main.get_all_posts"))
    return render_template("register.html", form=form, current_user=current_user)


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        result = db.session.execute(
            db.select(User).where(User.email == form.email.data)
        )
        user = result.scalar()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for("main.login"))
        elif not check_password_hash(user.password, form.password.data):
            flash("Password incorrect, please try again.")
            return redirect(url_for("main.login"))
        else:
            login_user(user)
            return redirect(url_for("main.get_all_posts"))
    return render_template("login.html", form=form, current_user=current_user)


@main_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.get_all_posts"))


# --- Blog routes ---

@main_bp.route("/")
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts, current_user=current_user)


@main_bp.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("main.login"))
        new_comment = Comment(
            text=comment_form.comment_text.data,
            comment_author=current_user,
            parent_post=requested_post,
        )
        db.session.add(new_comment)
        db.session.commit()
    return render_template(
        "post.html", post=requested_post, current_user=current_user, form=comment_form
    )


@main_bp.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y"),
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("main.get_all_posts"))
    return render_template("make-post.html", form=form, current_user=current_user)


@main_bp.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body,
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("main.show_post", post_id=post.id))
    return render_template(
        "make-post.html", form=edit_form, is_edit=True, current_user=current_user
    )


@main_bp.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for("main.get_all_posts"))


@main_bp.route("/about")
def about():
    return render_template("about.html", current_user=current_user)


@main_bp.route("/contact")
def contact():
    return render_template("contact.html", current_user=current_user)


# --- Video upload + Kaggle orchestration ---

def _update_kaggle_dataset(video_file_path: str) -> bool:
    """Copy video to local Kaggle dataset folder and push a new version."""
    dataset_folder = current_app.config.get(
        "KAGGLE_DATASET_FOLDER",
        os.path.join(os.getcwd(), "kaggle_dataset_folder"),
    )
    try:
        shutil.copy(video_file_path, dataset_folder)
        result = subprocess.run(
            ["kaggle", "datasets", "version", "-p", dataset_folder, "-m", "New video upload"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print("[Kaggle] Dataset updated successfully.")
            return True
        else:
            print(f"[Kaggle] Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"[Kaggle] Exception: {e}")
        return False


def _run_kaggle_notebook_selenium() -> bool:
    """Launch or reuse a Selenium session to trigger the Kaggle notebook."""
    global _global_driver

    try:
        import undetected_chromedriver as uc
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        kernel_url = "https://www.kaggle.com/code/txctyg/videoconv/edit"

        if _upload_counter == 0 or _global_driver is None:
            chrome_options = uc.ChromeOptions()
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            driver = uc.Chrome(options=chrome_options)

            # Login to Kaggle via Google OAuth
            driver.get("https://www.kaggle.com/account/login")
            LOGIN_BTN = (By.CSS_SELECTOR, '[class="sc-hJRrWL iwZBhE"]')
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable(LOGIN_BTN)).click()

            EMAIL_INPUT = (By.CSS_SELECTOR, '[aria-label="Email or phone"]')
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable(EMAIL_INPUT)
            ).send_keys(os.getenv("KAGGLE_EMAIL", ""))

            buttons = driver.find_elements(By.CSS_SELECTOR, '[jsname="V67aGc"]')
            for btn in buttons:
                if btn.text.strip() == "Next":
                    btn.click()
                    break

            PASSWORD = (By.CSS_SELECTOR, '[aria-label="Enter your password"]')
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable(PASSWORD)
            ).send_keys(os.getenv("KAGGLE_PASSWORD", ""))

            buttons = driver.find_elements(By.CSS_SELECTOR, '[jsname="V67aGc"]')
            for btn in buttons:
                if btn.text.strip() == "Next":
                    btn.click()
                    break

            time.sleep(6)
            driver.get(kernel_url)
            time.sleep(13)
            _global_driver = driver
        else:
            driver = _global_driver

        # Click dataset actions -> check for updates -> update -> run all
        BRO123_BTN = (By.CSS_SELECTOR, '[aria-label="More actions for (Bro123)"]')
        element = WebDriverWait(driver, 20).until(EC.presence_of_element_located(BRO123_BTN))
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(3)
        driver.execute_script("arguments[0].click();", element)

        check_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//p[normalize-space()="Check for updates"]'))
        )
        driver.execute_script("arguments[0].click();", check_btn)

        update_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//*[normalize-space()='Update']"))
        )
        update_btn.click()
        time.sleep(13)

        run_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//*[normalize-space()='Run All']"))
        )
        run_btn.click()

        print("[Selenium] Kaggle notebook triggered.")
        return True

    except Exception as e:
        print(f"[Selenium] Error: {e}")
        return False


@main_bp.route("/upload", methods=["GET", "POST"])
def upload_file():
    if not current_user.is_authenticated:
        flash("You must be logged in to upload files.")
        return jsonify({"error": "Unauthorized access. Please log in."}), 403

    global _upload_counter, _final_summary

    # Handle output callback from Kaggle notebook
    if request.method == "POST" and "output" in request.form:
        output = request.form.get("output")
        print(f"[Upload] Received output from Kaggle: {output[:200]}...")

        final_prompt = (
            f"Here are my snippet summaries: {output} "
            f"Please combine these snippets into one cohesive summary."
        )

        try:
            import undetected_chromedriver as uc
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            chrome_options = uc.ChromeOptions()
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chatgpt_driver = uc.Chrome(options=chrome_options)
            chatgpt_driver.get("https://chatgpt.com")

            CHAT_BOX = (By.CSS_SELECTOR, '[data-placeholder="Ask anything"]')
            WebDriverWait(chatgpt_driver, 20).until(
                EC.element_to_be_clickable(CHAT_BOX)
            ).send_keys(final_prompt)

            SEND_BTN = (By.CSS_SELECTOR, '[data-testid="send-button"]')
            WebDriverWait(chatgpt_driver, 20).until(
                EC.element_to_be_clickable(SEND_BTN)
            ).click()

            time.sleep(10)
            RESPONSE = (
                By.CSS_SELECTOR,
                '[class="markdown prose w-full break-words dark:prose-invert dark"]',
            )
            output_element = WebDriverWait(chatgpt_driver, 30).until(
                EC.presence_of_element_located(RESPONSE)
            )
            _final_summary = output_element.text
            chatgpt_driver.quit()
            return jsonify({"summary": _final_summary}), 200
        except Exception as e:
            print(f"[ChatGPT] Error: {e}")
            return jsonify({"error": str(e)}), 500

    # Handle file upload from user
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part in form.")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("No selected file.")
            return redirect(request.url)

        if file and _allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            flash(f"File saved at {filepath}")

            ds_success = _update_kaggle_dataset(filepath)
            if ds_success:
                flash("Video uploaded & Kaggle dataset updated!")
                kernel_success = _run_kaggle_notebook_selenium()
                if kernel_success:
                    flash("Kaggle notebook triggered successfully!")
                else:
                    flash("Kaggle notebook trigger failed.")
                _upload_counter += 1
                return jsonify({"summary": _final_summary}), 200
            else:
                flash("Video uploaded, but dataset update failed.")
                return jsonify({"error": "Dataset update failed."}), 500

    return render_template("upload.html")
