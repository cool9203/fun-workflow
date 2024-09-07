echo "----------Start unittest----------"
coverage run -m unittest discover
echo "----------End unittest----------"

echo "----------Code coverage----------"
coverage report -m
