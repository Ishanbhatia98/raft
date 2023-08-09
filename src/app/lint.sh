path=${1:-.}
echo "Linting $path"
isort $path
black $path

