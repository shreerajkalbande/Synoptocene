import os
import subprocess
import shutil
from datetime import date
from flask import (
    Flask,
    abort,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify,
)
from flask_bootstrap import Bootstrap4
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Import your forms from the forms.py
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_KEY")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_secret_key_here")  # Keep this secret

ckeditor = CKEditor(app)
Bootstrap4(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"mp4", "avi", "mov"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# For adding profile images to the comment section
gravatar = Gravatar(
    app,
    size=100,
    rating="g",
    default="retro",
    force_default=False,
    force_lower=False,
    use_ssl=False,
    base_url=None,
)


# -----------------------
# DATABASE SETUP
# -----------------------
class Base(DeclarativeBase):
    pass


app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DB_URI", "sqlite:///posts.db")
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# -----------------------
# TABLES
# -----------------------
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    comments = relationship("Comment", back_populates="parent_post")


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")


class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")
    post_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")


with app.app_context():
    db.create_all()


# -----------------------
# DECORATORS
# -----------------------
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


# -----------------------
# ROUTES
# -----------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        result = db.session.execute(
            db.select(User).where(User.email == form.email.data)
        )
        user = result.scalar()
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for("login"))

        hash_and_salted_password = generate_password_hash(
            form.password.data, method="pbkdf2:sha256", salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("get_all_posts"))
    return render_template("register.html", form=form, current_user=current_user)


# 1) Folder where you keep your local Kaggle dataset mirror:
KAGGLE_DATASET_FOLDER = os.path.join(os.getcwd(), "kaggle_dataset_folder")

# # 2) Folder containing your .ipynb + kernel-metadata.json:
# KAGGLE_KERNEL_FOLDER = os.path.join(os.getcwd(), "")
chatgpt_driver = None
global_driver = None
upload_counter = 0  # 0 means first upload
final_summary = None
# Global variable for the ChatGPT driver


def update_kaggle_dataset(video_file_path):
    """
    Copies the new video into your local Kaggle dataset folder,
    then creates a new dataset version on Kaggle.
    """
    try:
        # Copy the uploaded video into the local dataset mirror
        shutil.copy(video_file_path, KAGGLE_DATASET_FOLDER)
        print(f"✅ Copied {video_file_path} to {KAGGLE_DATASET_FOLDER}.")

        # 'kaggle datasets version' to create a new dataset version
        cmd = [
            "kaggle",  # or full path to 'kaggle' if needed
            "datasets",
            "version",
            "-p",
            KAGGLE_DATASET_FOLDER,
            "-m",
            "New video upload",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Kaggle dataset updated successfully!")
            print(result.stdout)
            return True
        else:
            print("❌ Error updating Kaggle dataset:", result.stderr)
            return False

    except Exception as e:
        print("❌ Exception during Kaggle dataset update:", str(e))
        return False


def run_kaggle_notebook_selenium():
    """
    1) Launches Chrome via Selenium and logs into Kaggle (only on the first upload).
    2) Navigates to the specified kernel_url.
    3) On subsequent uploads, reuses the existing Selenium session,
       refreshes the page, and clicks the necessary buttons (e.g., "More actions",
       "Check for updates", "Update", "Run All") without opening a new window.
    """
    global global_driver

    try:
        import undetected_chromedriver as uc
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time

        # If this is the first upload, create a new driver and log in
        if upload_counter == 0 or global_driver is None:
            chrome_options = uc.ChromeOptions()
            # chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            driver = uc.Chrome(options=chrome_options)
            # # 1. Navigate to Kaggle login page
            driver.get("https://www.kaggle.com/account/login")
            # 2. Login steps (as before):
            LOGIN_BTN = (By.CSS_SELECTOR, '[class="sc-hJRrWL iwZBhE"]')
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable(LOGIN_BTN)
            ).click()
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
            driver.get("https://www.kaggle.com/code/txctyg/videoconv/edit")
            time.sleep(13)

            # Click "More actions for (Bro123)" button (first time)
            BRO123_BUTTON = (
                By.CSS_SELECTOR,
                '[aria-label="More actions for (Bro123)"]',
            )
            element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(BRO123_BUTTON)
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(3)
            driver.execute_script("arguments[0].click();", element)

            # Click "Check for updates" button
            check_updates_btn = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//p[normalize-space()="Check for updates"]')
                )
            )
            driver.execute_script("arguments[0].click();", check_updates_btn)

            # Click "Update" button
            RUN_ALL_XPATH = (By.XPATH, "//*[normalize-space()='Update']")
            element = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable(RUN_ALL_XPATH)
            )
            element.click()
            time.sleep(13)
            # Click "Run All" button
            RUN_ALL_XPATH = (By.XPATH, "//*[normalize-space()='Run All']")
            element = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable(RUN_ALL_XPATH)
            )
            element.click()

            global_driver = driver  # Save for later reuse
            print("✅ New Selenium session created and initial actions performed.")

            # This will download all files, remove everything except "final_output.txt",
            # and print its contents if found.

        else:
            # For subsequent uploads, reuse the existing Selenium driver
            driver = global_driver
            print("Reusing existing Selenium session.")
            # driver.refresh()  # refresh the current page
            # time.sleep(10)  # wait for the page to reload completely

            # Click "More actions for (Bro123)" again
            BRO123_BUTTON = (
                By.CSS_SELECTOR,
                '[aria-label="More actions for (Bro123)"]',
            )
            element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(BRO123_BUTTON)
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(3)
            driver.execute_script("arguments[0].click();", element)

            # Click "Check for updates" button
            check_updates_btn = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//p[normalize-space()="Check for updates"]')
                )
            )
            driver.execute_script("arguments[0].click();", check_updates_btn)

            # Click "Update" button
            RUN_ALL_XPATH = (By.XPATH, "//*[normalize-space()='Update']")
            element = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable(RUN_ALL_XPATH)
            )
            element.click()
            time.sleep(12)
            # Click "Run All" button
            RUN_ALL_XPATH = (By.XPATH, "//*[normalize-space()='Run All']")
            element = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable(RUN_ALL_XPATH)
            )
            element.click()
            print("✅ Existing Selenium session refreshed and actions re-triggered.")

    except Exception as e:
        print("❌ An error occurred in run_kaggle_notebook_selenium:", str(e))
        return False

    return True


@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if not current_user.is_authenticated:  # Check if user is logged in
        flash("You must be logged in to upload files.")
        return (
            jsonify({"error": "Unauthorized access. Please log in."}),
            403,
        )  # Forbidden

    global chatgpt_driver, upload_counter, final_summary

    # ✅ First, check if Kaggle is just sending output
    if request.method == "POST" and "output" in request.form:
        output = request.form.get("output")
        print("📥 Received output from Kaggle:", output)
        final_prompt = (f"Here are my snippet summaries: {output} "
                        f"Please combine these snippets into one cohesive summary.")

        import undetected_chromedriver as uc
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time

        print("Initializing ChatGPT driver and performing login...")
        chrome_options = uc.ChromeOptions()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chatgpt_driver = uc.Chrome(options=chrome_options)
        chatgpt_driver.get("https://chatgpt.com")

        # time.sleep(random.uniform(2, 4))
        #
        # # Perform login steps...
        # # LOGIN_BTN = (By.CSS_SELECTOR, '[data-testid="login-button"]')
        # # WebDriverWait(chatgpt_driver, 20).until(EC.element_to_be_clickable(LOGIN_BTN)).click()
        # login_btn = chatgpt_driver.find_element(By.CSS_SELECTOR, '[data-testid="login-button"]')
        #
        # # Create an ActionChains instance
        # actions = ActionChains(chatgpt_driver)
        #
        # # Move to the element, pause, then click it
        # actions.move_to_element(login_btn).pause(random.uniform(0.5, 1
        # .5)).click(login_btn).perform()
        # # EMAIL_INPUT = (By.CSS_SELECTOR, '[id="email-input"]')
        # # WebDriverWait(chatgpt_driver, 20
        # ).until(EC.element_to_be_clickable(EMAIL_INPUT)).send_keys(
        # #     os.getenv("CHATGPT_EMAIL", ""))
        #
        # # NEXTBUTTON = (By.CSS_SELECTOR, 'input.continue-btn')
        # # WebDriverWait(chatgpt_driver, 20).until(EC.element_to_be_clickable(NEXTBUTTON)).click()
        # time.sleep(random.uniform(2, 4))
        #
        # EMAIL_INPUT = (By.CSS_SELECTOR, '[id="email-input"]')
        # email_input_elem = WebDriverWait(chatgpt_driver, 20
        # ).until(EC.element_to_be_clickable(EMAIL_INPUT))
        # actions.move_to_element(email_input_elem).pause(random.uniform(0.5, 1.0)).send_keys(
        #     os.getenv("CHATGPT_EMAIL", "")).perform()
        #
        # # # Wait until at least one Next button is present
        # # WebDriverWait(chatgpt_driver, 15).until(
        # #     EC.presence_of_element_located((By.CSS_SELECTOR, '[jsname="V67aGc"]'))
        # # )
        # # time.sleep(random.uniform(2, 4))
        #
        # buttons = chatgpt_driver.find_elements(By.CSS_SELECTOR, '.continue-btn')
        # found = False
        # for btn in buttons:
        #     btn_value = btn.get_attribute("value")
        #     print("Found button with value:", btn_value)
        #     if btn_value and btn_value.strip().lower() == "continue":
        #         found = True
        #         print("Button location:", btn.location)
        #         print("Button size:", btn.size)
        #         if btn.is_displayed():
        #             print("Button is displayed.")
        #         else:
        #             print("Button is NOT displayed.")
        #
        #         try:
        #             actions = ActionChains(chatgpt_driver)
        #             actions.move_to_element(btn).pause(ran
        #             dom.uniform(0.5, 1.5)).click(btn).perform()
        #             print("Button clicked successfully.")
        #         except Exception as e:
        #             print("Failed to click button:", str(e))
        #         break
        #
        # if not found:
        #     print("No button with value 'Continue' found.")
        #
        # captcha_locator = (By.CSS_SELECTOR, '.captcha-overlay')
        #
        # try:
        #     # Wait up to 60 seconds for the captcha overlay to vanish.
        #     WebDriverWait(chatgpt_driver, 120).until(
        #         EC.invisibility_of_element_located(captcha_locator)
        #     )
        #     print("Captcha has disappeared.")
        # except TimeoutException:
        #     print("Captcha did not disappear within 60 seconds. Proceeding anyway.")
        # try:
        #     # Wait for the password input field to be visible
        #     password_input = WebDriverWait(chatgpt_driver, 40).until(
        #         EC.visibility_of_element_located((By.CSS_SELECTOR, "input#password"))
        #     )
        #     password_input.send_keys(os.getenv("CHATGPT_PASSWORD", ""))
        #     print("Password typed successfully.")
        # except TimeoutException:
        #     print("Timeout waiting for password input field to become visible.")
        #
        # # # Now wait for the actual password input to become visible.
        # # # Often it might be an <input> with type="password".
        # # password_input = WebDriverWait(chatgpt_driver, 20).until(
        # #     EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
        # # )
        # # password_input.send_keys(os.getenv("CHATGPT_PASSWORD", ""))
        # # print("Password typed successfully.")
        # # Define the PASSWORD locator
        # # PASSWORD = (By.CSS_SELECTOR, '[id="password"]')
        # #
        # # # Increase wait time if needed (e.g., 40 seconds instead of 20)
        # # try:
        # #     print("Waiting for the password field to become clickable...")
        # #     password_elem = WebDriverWait(chatgpt_driver, 40).until(
        # #         EC.element_to_be_clickable(PASSWORD)
        # #     )
        # #     print("Password field is clickable. Typing password...")
        # #     password_elem.send_keys(os.getenv("CHATGPT_PASSWORD", ""))
        # #     print("Password typed successfully.")
        # # except TimeoutException as e:
        # #     print("Timeout waiting for password field to be clickable.")
        # #     # Optionally, try to check if the element exists:
        # #     elems = chatgpt_driver.find_elements(By.CSS_SELECTOR, '[id="password"]')
        # #     if elems:
        # #         print("Found password field elements:", len(elems))
        # #     else:
        # #         print("No password field element found.")
        # #     # As a fallback, you can try clicking via JavaScript if needed:
        # #     try:
        # #         if elems:
        # #             chatgpt_driver.execute_script("arguments[0].click();", elems[0])
        # #             elems[0].send_keys("")
        # #             print("Password typed via JavaScript click fallback.")
        # #     except Exception as js_e:
        # #         print("Fallback method also failed:", str(js_e))
        # # PASSWORD = (By.CSS_SELECTOR, '[id="password"]')
        # # WebDriverWait(chatgpt_driver, 20).until(EC.element_to_be_cli
        # ckable(PASSWORD)).send_keys("")
        #
        # SUBMIT = (By.CSS_SELECTOR, '[name="action"]')
        # WebDriverWait(chatgpt_driver, 20).until(EC.element_to_be_clickable(SUBMIT)).click()
        #
        # REASON = (By.CSS_SELECTOR, '[aria-label="Reason"]')
        # WebDriverWait(chatgpt_driver, 10).until(EC.element_to_be_clickable(REASON)).click()
        # print("ChatGPT driver initialized and logged in.")

        # driver = chatgpt_driver
        # driver.get("https://chatgpt.com/")

        CHAT_BOX = (By.CSS_SELECTOR, '[data-placeholder="Ask anything"]')
        WebDriverWait(chatgpt_driver, 20).until(
            EC.element_to_be_clickable(CHAT_BOX)
        ).send_keys(final_prompt)

        SEND_BTN = (By.CSS_SELECTOR, '[data-testid="send-button"]')
        WebDriverWait(chatgpt_driver, 20).until(
            EC.element_to_be_clickable(SEND_BTN)
        ).click()
        time.sleep(10)
        RESPONSE_LOCATOR = (
            By.CSS_SELECTOR,
            '[class="markdown prose w-full break-words dark:prose-invert dark"]',
        )
        output_element = WebDriverWait(chatgpt_driver, 30).until(
            EC.presence_of_element_located(RESPONSE_LOCATOR)
        )
        final_summary = output_element.text
        print("Final Combined Summary:", final_summary)
        chatgpt_driver.quit()
        return jsonify({"summary": final_summary}), 200

    # ✅ Then check for a file upload from the user
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part in form.")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            flash("No selected file.")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            flash(f"File saved at {filepath}")

            # Step 1: Update Kaggle dataset
            ds_success = update_kaggle_dataset(filepath)
            if ds_success:
                flash("Video uploaded & Kaggle dataset updated!")
                # Step 2: Run or refresh the Kaggle notebook via Selenium
                kernel_success = run_kaggle_notebook_selenium()
                if kernel_success:
                    flash("Kaggle notebook re-run triggered successfully!")
                else:
                    flash("Kaggle notebook run failed or did not complete.")
                upload_counter += 1
                # Replace with actual summary
                # Return JSON response with the summary so that the frontend can display it.
                return jsonify({"summary": final_summary}), 200
            else:
                flash("Video uploaded, but dataset update failed.")
                return jsonify({"error": "Dataset update failed."}), 500

    # Render upload form for GET requests
    return render_template("upload.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(
            db.select(User).where(User.email == form.email.data)
        )
        user = result.scalar()

        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for("login"))
        elif not check_password_hash(user.password, password):
            flash("Password incorrect, please try again.")
            return redirect(url_for("login"))
        else:
            login_user(user)
            return redirect(url_for("get_all_posts"))

    return render_template("login.html", form=form, current_user=current_user)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("get_all_posts"))


@app.route("/")
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts, current_user=current_user)


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

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


@app.route("/new-post", methods=["GET", "POST"])
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
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, current_user=current_user)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
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
        return redirect(url_for("show_post", post_id=post.id))
    return render_template(
        "make-post.html", form=edit_form, is_edit=True, current_user=current_user
    )


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for("get_all_posts"))


@app.route("/about")
def about():
    return render_template("about.html", current_user=current_user)


@app.route("/contact")
def contact():
    return render_template("contact.html", current_user=current_user)


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
